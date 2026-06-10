import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.crawler.fetcher import download_file, fetch_html
from app.crawler.parser import (
    content_hash,
    extract_article_content,
    extract_list_items,
    parse_date,
    parse_date_from_url,
    resolve_item_date,
)
from app.models.article import Article, ArticleAttachment, PolicyLevel, ProjectCategory
from app.models.monitor import ColumnType, CrawlFilterMode, CrawlTask, MonitorColumn, SourceStatus, SourceType
from app.services.crawl_filter import matches_crawl_filter
from app.models.user import CrawlLog
from app.services.push_service import match_and_push
from app.services.search_service import search_service

logger = logging.getLogger(__name__)
settings = get_settings()


async def schedule_article_analysis(article_id: int) -> None:
    """触发文章 AI 分析。本地 eager 模式在同一事件循环内后台执行，避免 Celery 线程池破坏 SQLAlchemy 异步上下文。"""
    from app.database import async_session_factory
    from app.services.ai_analyze_service import analyze_article_record

    async def _run() -> None:
        async with async_session_factory() as db:
            try:
                await analyze_article_record(db, article_id)
                await db.commit()
            except Exception:
                logger.exception("AI 分析失败 article_id=%s", article_id)

    if settings.celery_eager:
        try:
            asyncio.get_running_loop()
            asyncio.create_task(_run())
            return
        except RuntimeError:
            pass

    try:
        from app.tasks.ai_tasks import analyze_article_task

        analyze_article_task.delay(article_id)
    except Exception:
        logger.exception("调度 AI 分析失败 article_id=%s", article_id)


class CrawlEngine:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _resolve_owner(
        self,
        filter_source: CrawlTask | MonitorColumn,
        explicit_owner_id: int | None = None,
    ) -> int | None:
        if isinstance(filter_source, CrawlTask) and filter_source.owner_id:
            return filter_source.owner_id
        return explicit_owner_id

    async def crawl_column(
        self,
        column_id: int,
        *,
        filter_ctx: CrawlTask | MonitorColumn | None = None,
        owner_id: int | None = None,
    ) -> dict:
        result = await self.db.execute(
            select(MonitorColumn)
            .options(selectinload(MonitorColumn.source))
            .where(MonitorColumn.id == column_id)
        )
        column = result.scalar_one_or_none()
        if not column:
            return {"status": "skipped", "new": 0, "updated": 0}
        filter_source = filter_ctx or column
        effective_owner = self._resolve_owner(filter_source, owner_id)
        source_type = column.source.type if column.source else None
        source_name = column.source.name if column.source else None
        source_status = column.source.status if column.source else None

        if filter_ctx is None and not column.is_active:
            return {"status": "skipped", "new": 0, "updated": 0}
        if filter_ctx is None and source_status != SourceStatus.ACTIVE:
            return {"status": "skipped", "new": 0, "updated": 0}

        new_count = 0
        updated_count = 0
        skipped_by_filter = 0
        list_count = 0
        error_message = None
        filter_mode = getattr(filter_source, "crawl_filter_mode", None) or CrawlFilterMode.COLUMN

        try:
            list_html = await fetch_html(column.column_url, use_playwright=column.use_playwright)
            list_items = extract_list_items(list_html, column.column_url, column.list_selector)
            list_count = len(list_items)

            for item in list_items:
                item_date = item.get("publish_time") or resolve_item_date(
                    item.get("date_text"), item.get("url")
                )
                if filter_mode == CrawlFilterMode.DATE_RANGE:
                    if item_date and not matches_crawl_filter(
                        filter_source, item.get("title", ""), publish_time=item_date
                    ):
                        skipped_by_filter += 1
                        continue
                elif filter_mode == CrawlFilterMode.COLUMN and not matches_crawl_filter(
                    filter_source, item.get("title", ""), publish_time=item_date
                ):
                    skipped_by_filter += 1
                    continue

                try:
                    async with self.db.begin_nested():
                        outcome = await self._process_article(
                            column,
                            item,
                            filter_source,
                            effective_owner,
                            source_type=source_type,
                            source_name=source_name,
                        )
                except Exception as exc:
                    logger.warning(
                        "栏目 %s 单条文章处理失败 %s: %s", column_id, item.get("url"), exc
                    )
                    continue
                if outcome == "new":
                    new_count += 1
                elif outcome == "updated":
                    updated_count += 1
                elif outcome is None and filter_mode in (
                    CrawlFilterMode.DATE_RANGE,
                    CrawlFilterMode.KEYWORD,
                ):
                    skipped_by_filter += 1

            await self.db.execute(
                update(MonitorColumn)
                .where(MonitorColumn.id == column_id)
                .values(last_crawled_at=datetime.now(timezone.utc))
            )
        except Exception as exc:
            error_message = str(exc)
            logger.exception("栏目 %s 采集失败", column_id)

        self.db.add(
            CrawlLog(
                owner_id=effective_owner,
                column_id=column_id,
                status="success" if not error_message else "failed",
                new_count=new_count,
                updated_count=updated_count,
                error_message=error_message,
            )
        )

        hint = None
        if not error_message and list_count == 0:
            hint = "列表页未解析到文章，请检查栏目 URL 是否与官网实际板块一致"
        elif not error_message and new_count == 0 and updated_count == 0 and skipped_by_filter:
            if filter_mode == CrawlFilterMode.DATE_RANGE:
                filter_label = "时间"
            elif filter_mode == CrawlFilterMode.KEYWORD:
                filter_label = "关键词"
            else:
                filter_label = "筛选"
            hint = f"共发现 {list_count} 条列表项，{skipped_by_filter} 条未通过{filter_label}筛选"

        return {
            "status": "success" if not error_message else "failed",
            "new": new_count,
            "updated": updated_count,
            "listed": list_count,
            "skipped_by_filter": skipped_by_filter,
            "hint": hint,
            "error": error_message,
        }

    async def _process_article(
        self,
        column: MonitorColumn,
        item: dict,
        filter_source: CrawlTask | MonitorColumn,
        owner_id: int | None,
        *,
        source_type: SourceType | None,
        source_name: str | None,
    ) -> str | None:
        url = item["url"]
        q = select(Article).where(Article.article_url == url)
        if owner_id is not None:
            q = q.where(Article.owner_id == owner_id)
        result = await self.db.execute(q)
        existing = result.scalar_one_or_none()

        detail_html = await fetch_html(url, use_playwright=column.use_playwright)
        parsed = extract_article_content(
            detail_html,
            url,
            title_selector=column.title_selector,
            content_selector=column.content_selector,
            date_selector=column.date_selector,
        )

        title = parsed["title"] or item["title"]
        content = parsed["content"] or ""
        publish_time = (
            parsed["publish_time"]
            or item.get("publish_time")
            or resolve_item_date(item.get("date_text"), url)
            or parse_date_from_url(url)
        )
        if not matches_crawl_filter(filter_source, title, content, publish_time):
            return None
        new_hash = content_hash(content or title)

        if existing:
            if existing.content_hash == new_hash:
                return None
            existing.title = title
            existing.content = content
            existing.publish_time = publish_time or existing.publish_time
            existing.publisher = parsed["publisher"] or existing.publisher
            existing.content_hash = new_hash
            existing.updated_at = datetime.now(timezone.utc)
            article = existing
            outcome = "updated"
        else:
            policy_level = PolicyLevel.UNKNOWN
            project_category = None
            if source_type == SourceType.MOE:
                policy_level = PolicyLevel.NATIONAL
            elif source_type == SourceType.PROVINCIAL:
                policy_level = PolicyLevel.PROVINCIAL
            if column.column_type == ColumnType.PROJECT_APPLY:
                project_category = (
                    ProjectCategory.NATIONAL
                    if policy_level == PolicyLevel.NATIONAL
                    else ProjectCategory.PROVINCIAL
                )
            elif column.column_type == ColumnType.POLICY:
                project_category = (
                    ProjectCategory.NATIONAL
                    if policy_level == PolicyLevel.NATIONAL
                    else ProjectCategory.PROVINCIAL
                )
            elif column.column_type == ColumnType.NOTICE:
                project_category = ProjectCategory.OTHER

            article = Article(
                owner_id=owner_id,
                column_id=column.id,
                title=title,
                content=content,
                publish_time=publish_time,
                publisher=parsed["publisher"],
                source_name=source_name,
                article_url=url,
                content_hash=new_hash,
                policy_level=policy_level,
                project_category=project_category,
            )
            self.db.add(article)
            try:
                async with self.db.begin_nested():
                    await self.db.flush()
                outcome = "new"
            except IntegrityError:
                result = await self.db.execute(q)
                dup = result.scalar_one_or_none()
                if dup:
                    if dup.content_hash == new_hash:
                        return None
                    dup.title = title
                    dup.content = content
                    dup.publish_time = publish_time or dup.publish_time
                    dup.publisher = parsed["publisher"] or dup.publisher
                    dup.content_hash = new_hash
                    dup.updated_at = datetime.now(timezone.utc)
                    article = dup
                    outcome = "updated"
                else:
                    logger.info("跳过重复 URL: %s", url)
                    return None

        await self._save_attachments(article, parsed.get("attachments", []))
        await self.db.flush()

        if outcome == "new":
            try:
                await match_and_push(self.db, article)
            except Exception:
                logger.exception("关键词推送失败 article=%s", article.id)

        if outcome == "new":
            await schedule_article_analysis(article.id)
        return outcome

    async def _save_attachments(self, article: Article, attachments: list[dict]) -> None:
        attach_dir = Path(settings.attachment_dir) / str(article.id)
        attach_dir.mkdir(parents=True, exist_ok=True)

        for att in attachments:
            result = await self.db.execute(
                select(ArticleAttachment).where(
                    ArticleAttachment.article_id == article.id,
                    ArticleAttachment.file_url == att["file_url"],
                )
            )
            if result.scalar_one_or_none():
                continue

            local_path = None
            try:
                filename = att["file_name"] or f"file.{att.get('file_type', 'bin')}"
                safe_name = "".join(c for c in filename if c.isalnum() or c in "._-（）()")[:200]
                local_path = str(attach_dir / safe_name)
                await download_file(att["file_url"], local_path)
            except Exception:
                local_path = None

            self.db.add(
                ArticleAttachment(
                    article_id=article.id,
                    file_name=att["file_name"],
                    file_url=att["file_url"],
                    file_type=att.get("file_type"),
                    local_path=local_path,
                )
            )


async def crawl_column(
    db: AsyncSession,
    column_id: int,
    *,
    filter_ctx: CrawlTask | MonitorColumn | None = None,
    owner_id: int | None = None,
) -> dict:
    engine = CrawlEngine(db)
    return await engine.crawl_column(column_id, filter_ctx=filter_ctx, owner_id=owner_id)
