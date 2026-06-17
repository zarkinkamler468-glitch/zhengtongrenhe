"""文章 AI 分析（供 API 直连与 Celery 任务共用）"""
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.key_info_extractor import refine_key_info
from app.ai.service import ai_service
from app.models.analysis import AIAnalysis
from app.models.article import Article, PolicyLevel, ProjectCategory
from app.models.user import User
from app.services.article_service import query_article_ids
from app.services.push_service import match_and_push
from app.services.quota_service import try_consume_ai
from app.services.search_service import search_service


def _infer_project_category(data: dict) -> ProjectCategory | None:
    tags = data.get("tags") or {}
    policy_type = str(tags.get("policy_type", ""))
    industry = str(tags.get("industry", ""))

    if any(k in policy_type for k in ("项目申报", "申报", "课题")):
        if "国家" in policy_type or "国家级" in str(tags.get("level", "")):
            return ProjectCategory.NATIONAL
        if "省" in policy_type or "省级" in str(tags.get("level", "")):
            return ProjectCategory.PROVINCIAL
        return ProjectCategory.OTHER
    if any(k in industry for k in ("科研", "研究", "课题")):
        return ProjectCategory.RESEARCH
    if any(k in industry for k in ("教学", "教改", "课程")):
        return ProjectCategory.TEACHING_REFORM
    if any(k in policy_type for k in ("政策", "文件", "办法")):
        level = str(tags.get("level", ""))
        if "国家" in level:
            return ProjectCategory.NATIONAL
        if "省" in level:
            return ProjectCategory.PROVINCIAL
    return ProjectCategory.OTHER


def apply_analysis_metadata(article: Article, data: dict) -> None:
    level_str = (data.get("tags") or {}).get("level", "")
    for key, val in {
        "国家级": PolicyLevel.NATIONAL,
        "省级": PolicyLevel.PROVINCIAL,
        "市级": PolicyLevel.MUNICIPAL,
        "校级": PolicyLevel.SCHOOL,
    }.items():
        if key in str(level_str):
            article.policy_level = val
            break
    article.project_category = _infer_project_category(data)


async def _load_billing_user(db: AsyncSession, owner_id: int | None) -> User | None:
    if not owner_id:
        return None
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == owner_id)
    )
    return result.scalar_one_or_none()


async def analyze_article_record(
    db: AsyncSession,
    article_id: int,
    *,
    force: bool = False,
    skip_billing: bool = False,
) -> dict:
    result = await db.execute(
        select(Article).options(selectinload(Article.analysis)).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        return {"status": "not_found", "article_id": article_id}

    if article.analysis:
        if not force:
            return {"status": "already_analyzed", "article_id": article_id}
        await db.execute(delete(AIAnalysis).where(AIAnalysis.article_id == article_id))
        await db.flush()
        article.analysis = None

    if not skip_billing:
        billing_user = await _load_billing_user(db, article.owner_id)
        if billing_user and not await try_consume_ai(db, billing_user):
            return {"status": "quota_exceeded", "article_id": article_id}

    data = await ai_service.analyze_article(
        article.title,
        article.content or "",
        publish_time=article.publish_time,
    )
    embedding = await ai_service.get_embedding(f"{article.title}\n{data.get('summary_300', '')}")

    apply_analysis_metadata(article, data)

    analysis = AIAnalysis(
        article_id=article.id,
        summary_100=data.get("summary_100"),
        summary_300=data.get("summary_300"),
        summary_page=data.get("summary_page"),
        tags=data.get("tags"),
        keywords=data.get("keywords"),
        key_info=data.get("key_info"),
        analysis=data.get("analysis"),
        json_result=data,
        embedding=embedding,
    )
    db.add(analysis)
    await db.flush()

    try:
        await search_service.index_article(article, analysis)
    except Exception:
        pass

    pushed = await match_and_push(db, article)
    return {
        "status": "success",
        "article_id": article_id,
        "pushed": pushed,
        "force": force,
    }


async def fix_article_key_info_record(db: AsyncSession, article_id: int) -> dict:
    result = await db.execute(
        select(Article)
        .options(selectinload(Article.analysis))
        .where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        return {"status": "not_found", "article_id": article_id}
    if not article.analysis:
        return {"status": "not_analyzed", "article_id": article_id}

    analysis = article.analysis
    old_info = dict(analysis.key_info or {})
    new_info = refine_key_info(
        article.content or "",
        analysis.key_info,
        publish_hint=article.publish_time,
    )
    if new_info == old_info:
        return {"status": "unchanged", "article_id": article_id}

    analysis.key_info = new_info
    if analysis.json_result:
        merged = dict(analysis.json_result)
        merged["key_info"] = new_info
        analysis.json_result = merged

    try:
        await search_service.index_article(article, analysis)
    except Exception:
        pass

    return {
        "status": "updated",
        "article_id": article_id,
        "old_deadline": old_info.get("deadline"),
        "new_deadline": new_info.get("deadline"),
    }


async def batch_fix_article_key_info(
    db: AsyncSession,
    user: User,
    *,
    article_ids: list[int] | None = None,
    source_name: str | None = None,
    policy_level: PolicyLevel | None = None,
    project_category: ProjectCategory | None = None,
    policy_type: str | None = None,
    q: str | None = None,
    limit: int = 200,
) -> dict:
    ids = await query_article_ids(
        db,
        user,
        article_ids=article_ids,
        source_name=source_name,
        policy_level=policy_level,
        project_category=project_category,
        policy_type=policy_type,
        q=q,
        has_analysis=True,
        limit=limit,
    )
    updated = 0
    unchanged = 0
    skipped = 0
    samples: list[dict] = []

    for article_id in ids:
        outcome = await fix_article_key_info_record(db, article_id)
        status = outcome.get("status")
        if status == "updated":
            updated += 1
            if len(samples) < 8:
                samples.append(outcome)
        elif status == "unchanged":
            unchanged += 1
        else:
            skipped += 1

    return {
        "status": "completed",
        "total": len(ids),
        "updated": updated,
        "unchanged": unchanged,
        "skipped": skipped,
        "samples": samples,
    }


async def batch_schedule_analyze(
    db: AsyncSession,
    user: User,
    *,
    force: bool = True,
    article_ids: list[int] | None = None,
    source_name: str | None = None,
    policy_level: PolicyLevel | None = None,
    project_category: ProjectCategory | None = None,
    policy_type: str | None = None,
    q: str | None = None,
    limit: int = 50,
) -> dict:
    has_analysis = True if force else None
    ids = await query_article_ids(
        db,
        user,
        article_ids=article_ids,
        source_name=source_name,
        policy_level=policy_level,
        project_category=project_category,
        policy_type=policy_type,
        q=q,
        has_analysis=has_analysis,
        limit=limit,
    )
    if not ids:
        return {"status": "empty", "count": 0, "article_ids": []}

    from app.services.tenant_scope import is_admin

    if not is_admin(user):
        remaining = max(0, user.ai_quota - user.ai_used)
        if len(ids) > remaining:
            return {
                "status": "quota_exceeded",
                "count": len(ids),
                "remaining": remaining,
            }

    return {"status": "ready", "count": len(ids), "article_ids": ids, "force": force}
