"""批量补采正文为空的文章（重新抓取详情页并更新数据库）。"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import or_, select

from app.crawler.fetcher import fetch_html
from app.crawler.parser import content_hash, extract_article_content
from app.database import async_session_factory
from app.models.analysis import AIAnalysis
from app.models.article import Article
from app.models.monitor import MonitorColumn
from app.services.ai_analyze_service import fix_article_key_info_record


async def backfill_article(db, article: Article, *, reanalyze: bool) -> dict:
    column = None
    if article.column_id:
        result = await db.execute(select(MonitorColumn).where(MonitorColumn.id == article.column_id))
        column = result.scalar_one_or_none()

    html = await fetch_html(article.article_url, use_playwright=bool(column and column.use_playwright))
    parsed = extract_article_content(
        html,
        article.article_url,
        title_selector=column.title_selector if column else None,
        content_selector=column.content_selector if column else None,
        date_selector=column.date_selector if column else None,
    )
    content = (parsed.get("content") or "").strip()
    if not content:
        return {"status": "still_empty", "article_id": article.id}

    article.title = parsed.get("title") or article.title
    article.content = content
    article.publish_time = parsed.get("publish_time") or article.publish_time
    article.publisher = parsed.get("publisher") or article.publisher
    article.content_hash = content_hash(content)
    await db.flush()

    outcome = {"status": "updated", "article_id": article.id, "content_len": len(content)}
    if reanalyze:
        has_analysis = await db.execute(
            select(AIAnalysis.id).where(AIAnalysis.article_id == article.id).limit(1)
        )
        if has_analysis.scalar_one_or_none():
            fix_result = await fix_article_key_info_record(db, article.id)
            outcome["key_info"] = fix_result.get("status")
    return outcome


async def main() -> None:
    parser = argparse.ArgumentParser(description="补采正文为空的文章")
    parser.add_argument("--limit", type=int, default=200, help="最多处理篇数")
    parser.add_argument("--source", type=str, default="", help="按来源名称过滤")
    parser.add_argument("--fix-key-info", action="store_true", help="同步修正 key_info")
    args = parser.parse_args()

    updated = 0
    still_empty = 0
    errors = 0

    async with async_session_factory() as db:
        q = (
            select(Article)
            .where(or_(Article.content.is_(None), Article.content == ""))
            .order_by(Article.id.desc())
            .limit(args.limit)
        )
        if args.source:
            q = q.where(Article.source_name.ilike(f"%{args.source}%"))
        result = await db.execute(q)
        articles = result.scalars().all()
        print(f"待补采 {len(articles)} 篇")

        for article in articles:
            try:
                outcome = await backfill_article(db, article, reanalyze=args.fix_key_info)
                status = outcome.get("status")
                if status == "updated":
                    updated += 1
                    print(f"OK #{article.id} {article.title[:40]} -> {outcome.get('content_len')} 字")
                else:
                    still_empty += 1
                    print(f"EMPTY #{article.id} {article.title[:40]}")
            except Exception as exc:
                errors += 1
                await db.rollback()
                print(f"ERR #{article.id} {exc}")

        await db.commit()

    print(f"完成：更新 {updated}，仍为空 {still_empty}，失败 {errors}")


if __name__ == "__main__":
    asyncio.run(main())
