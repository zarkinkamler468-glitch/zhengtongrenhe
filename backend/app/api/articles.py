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

)

from app.config import get_settings
from app.services.ai_analyze_service import analyze_article_record
from app.services.article_service import get_article_overview, list_source_names, query_articles
from app.services.quota_service import consume_ai, ensure_ai_quota
from app.services.search_service import search_service
from app.services.tenant_scope import assert_article_access

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


