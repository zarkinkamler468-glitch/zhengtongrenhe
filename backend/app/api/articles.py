from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload



from app.database import get_db

from app.models.article import Article, PolicyLevel, ProjectCategory

from app.models.user import User, UserRoleEnum

from app.schemas.analysis import AIAnalysisOut

from app.schemas.article import (

    ArticleDetail,

    ArticleListResponse,

    ArticleOverview,

    ArticleSearchResult,

    AttachmentOut,

    BatchArticleActionBody,

)

from app.config import get_settings
from app.services.ai_analyze_service import (
    analyze_article_record,
    batch_fix_article_key_info,
    batch_schedule_analyze,
)
from app.services.article_service import get_article_overview, list_source_names, query_articles
from app.services.quota_service import consume_ai, ensure_ai_quota
from app.services.search_service import search_service
from app.services.tenant_scope import assert_article_access, is_admin

from app.tasks.ai_tasks import analyze_article_task

from app.utils.deps import require_roles

settings = get_settings()



router = APIRouter()





@router.get("/overview", response_model=ArticleOverview)

async def articles_overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    return await get_article_overview(db, user)





@router.get("/sources")

async def article_sources(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    return {"sources": await list_source_names(db, user)}





@router.get("", response_model=ArticleListResponse)

async def list_articles(

    skip: int = Query(0, ge=0),

    limit: int = Query(20, ge=1, le=100),

    policy_level: PolicyLevel | None = None,

    project_category: ProjectCategory | None = None,

    source_name: str | None = None,

    has_analysis: bool | None = None,

    policy_type: str | None = None,

    q: str | None = None,

    db: AsyncSession = Depends(get_db),

    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    total, items = await query_articles(
        db,
        user,
        skip=skip,

        limit=limit,

        policy_level=policy_level,

        project_category=project_category,

        source_name=source_name,

        has_analysis=has_analysis,

        policy_type=policy_type,

        q=q,

    )

    return ArticleListResponse(total=total, items=items)





@router.get("/search", response_model=ArticleSearchResult)

async def search_articles(

    q: str = Query(..., min_length=1),

    skip: int = Query(0, ge=0),

    limit: int = Query(20, ge=1, le=100),

    policy_level: PolicyLevel | None = None,

    db: AsyncSession = Depends(get_db),

    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    total, items = await search_service.search(db, q, skip, limit, policy_level=policy_level, user=user)

    return ArticleSearchResult(total=total, items=items, query=q)





@router.post("/batch/fix-deadlines")
async def batch_fix_deadlines(
    body: BatchArticleActionBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    """根据原文规则批量修正已分析文章的截止时间、发布时间及摘要中的日期（不调用 AI，不消耗配额）。"""
    limit = min(max(body.limit, 1), 500)
    try:
        result = await batch_fix_article_key_info(
            db,
            user,
            article_ids=body.article_ids,
            source_name=body.source_name,
            policy_level=body.policy_level,
            project_category=body.project_category,
            policy_type=body.policy_type,
            q=body.q,
            limit=limit,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"批量修正失败: {exc}") from exc





@router.post("/batch/analyze")
async def batch_analyze_articles(
    body: BatchArticleActionBody,
    force: bool = Query(True, description="为 true 时重新分析并覆盖已有结果"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    """批量调度 AI 重新分析（按当前筛选条件，单次最多 50 篇）。"""
    limit = min(max(body.limit, 1), 50)
    plan = await batch_schedule_analyze(
        db,
        user,
        force=force,
        article_ids=body.article_ids,
        source_name=body.source_name,
        policy_level=body.policy_level,
        project_category=body.project_category,
        policy_type=body.policy_type,
        q=body.q,
        limit=limit,
    )
    if plan["status"] == "empty":
        return plan
    if plan["status"] == "quota_exceeded":
        raise HTTPException(
            status_code=429,
            detail=f"AI 分析次数不足：剩余 {plan['remaining']} 次，本次需 {plan['count']} 次",
        )

    article_ids: list[int] = plan["article_ids"]

    if settings.celery_eager:
        results = []
        success = 0
        for article_id in article_ids:
            try:
                outcome = await analyze_article_record(
                    db, article_id, force=force, skip_billing=True
                )
                if outcome.get("status") == "success":
                    success += 1
                    if not is_admin(user):
                        await consume_ai(db, user)
                results.append(outcome)
            except Exception as exc:
                results.append({"status": "failed", "article_id": article_id, "error": str(exc)})
        return {
            "status": "completed",
            "count": len(article_ids),
            "success": success,
            "force": force,
            "results": results[:20],
        }

    for article_id in article_ids:
        if not is_admin(user):
            await consume_ai(db, user)
        analyze_article_task.delay(article_id, force=force, skip_billing=True)

    return {
        "status": "scheduled",
        "count": len(article_ids),
        "force": force,
        "article_ids": article_ids[:20],
    }





@router.get("/{article_id}", response_model=ArticleDetail)

async def get_article(

    article_id: int,

    db: AsyncSession = Depends(get_db),

    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    result = await db.execute(

        select(Article)

        .options(selectinload(Article.attachments), selectinload(Article.analysis))

        .where(Article.id == article_id)

    )

    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    try:
        assert_article_access(user, article)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    analysis_out = None

    if article.analysis:

        analysis_out = AIAnalysisOut.model_validate(article.analysis)



    return ArticleDetail(

        id=article.id,

        title=article.title,

        content=article.content,

        publish_time=article.publish_time,

        publisher=article.publisher,

        source_name=article.source_name,

        article_url=article.article_url,

        policy_level=article.policy_level,

        project_category=article.project_category,

        created_at=article.created_at,

        updated_at=article.updated_at,

        attachments=[AttachmentOut.model_validate(a) for a in article.attachments],

        analysis=analysis_out,

    )





@router.post("/{article_id}/analyze")
async def trigger_analyze_article(
    article_id: int,
    force: bool = Query(False, description="为 true 时重新分析并覆盖已有结果"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    result = await db.execute(
        select(Article)
        .options(selectinload(Article.analysis))
        .where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    try:
        assert_article_access(user, article)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if not force and article.analysis:
        return {"status": "already_analyzed", "article_id": article_id}

    ensure_ai_quota(user)

    if settings.celery_eager:
        try:
            result = await analyze_article_record(
                db, article_id, force=force, skip_billing=True
            )
            if result.get("status") == "quota_exceeded":
                raise HTTPException(status_code=429, detail="AI 分析次数已用尽，请联系管理员")
            if result.get("status") == "success":
                await consume_ai(db, user)
            return result
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"AI 分析失败: {exc}") from exc

    await consume_ai(db, user)
    task = analyze_article_task.delay(article_id, force=force, skip_billing=True)
    return {"status": "scheduled", "task_id": task.id, "force": force}


