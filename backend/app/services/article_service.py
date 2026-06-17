"""政策知识库：分类筛选、统计与列表查询"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analysis import AIAnalysis
from app.models.article import Article, PolicyLevel, ProjectCategory
from app.models.user import User
from app.schemas.article import ArticleListItem
from app.services.tenant_scope import scope_owner
from app.utils.sql_order import desc_nulls_last


def article_list_item(article: Article) -> ArticleListItem:
    analysis = article.analysis
    tags = analysis.tags if analysis else None
    return ArticleListItem(
        id=article.id,
        title=article.title,
        publish_time=article.publish_time,
        publisher=article.publisher,
        source_name=article.source_name,
        article_url=article.article_url,
        policy_level=article.policy_level,
        project_category=article.project_category,
        created_at=article.created_at,
        has_analysis=analysis is not None,
        summary_preview=analysis.summary_100 if analysis else None,
        policy_type=(tags or {}).get("policy_type") if tags else None,
        keywords=(analysis.keywords[:5] if analysis and analysis.keywords else None),
    )


async def query_articles(
    db: AsyncSession,
    user: User,
    *,
    skip: int = 0,
    limit: int = 20,
    policy_level: PolicyLevel | None = None,
    project_category: ProjectCategory | None = None,
    source_name: str | None = None,
    has_analysis: bool | None = None,
    policy_type: str | None = None,
    q: str | None = None,
) -> tuple[int, list[ArticleListItem]]:
    base = select(Article).options(selectinload(Article.analysis))
    base = scope_owner(base, Article, user)

    if policy_level:
        base = base.where(Article.policy_level == policy_level)
    if project_category:
        base = base.where(Article.project_category == project_category)
    if source_name:
        base = base.where(Article.source_name == source_name)
    if has_analysis is False:
        base = base.outerjoin(AIAnalysis, AIAnalysis.article_id == Article.id).where(AIAnalysis.id.is_(None))
    elif has_analysis is True or policy_type:
        base = base.join(AIAnalysis, AIAnalysis.article_id == Article.id)
        if policy_type:
            base = base.where(cast(AIAnalysis.tags, String).ilike(f"%{policy_type}%"))
    if q:
        like = f"%{q}%"
        base = base.where(
            or_(
                Article.title.ilike(like),
                Article.content.ilike(like),
                Article.source_name.ilike(like),
            )
        )

    count_q = select(func.count()).select_from(base.subquery())
    total = int((await db.execute(count_q)).scalar() or 0)

    result = await db.execute(
        base.order_by(*desc_nulls_last(Article.publish_time), Article.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    articles = result.scalars().unique().all()
    return total, [article_list_item(a) for a in articles]


async def get_article_overview(db: AsyncSession, user: User) -> dict:
    base = scope_owner(select(Article), Article, user)
    total = int((await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0)
    analyzed_q = (
        select(func.count(AIAnalysis.id))
        .select_from(Article)
        .join(AIAnalysis, AIAnalysis.article_id == Article.id)
    )
    analyzed_q = scope_owner(analyzed_q, Article, user)
    analyzed = int((await db.execute(analyzed_q)).scalar() or 0)

    level_q = select(Article.policy_level, func.count(Article.id)).group_by(Article.policy_level)
    level_q = scope_owner(level_q, Article, user)
    level_rows = await db.execute(level_q)
    by_level = {row[0].value: row[1] for row in level_rows.all()}

    cat_q = (
        select(Article.project_category, func.count(Article.id))
        .where(Article.project_category.isnot(None))
        .group_by(Article.project_category)
    )
    cat_q = scope_owner(cat_q, Article, user)
    cat_rows = await db.execute(cat_q)
    by_category = {row[0].value: row[1] for row in cat_rows.all() if row[0]}

    source_q = (
        select(Article.source_name, func.count(Article.id))
        .where(Article.source_name.isnot(None))
        .group_by(Article.source_name)
        .order_by(func.count(Article.id).desc())
        .limit(12)
    )
    source_q = scope_owner(source_q, Article, user)
    source_rows = await db.execute(source_q)
    top_sources = [{"name": row[0], "count": row[1]} for row in source_rows.all()]

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_q = select(func.count(Article.id)).where(Article.created_at >= week_ago)
    recent_q = scope_owner(recent_q, Article, user)
    recent = int((await db.execute(recent_q)).scalar() or 0)

    type_counts: dict[str, int] = {}
    type_q = (
        select(AIAnalysis.tags)
        .select_from(Article)
        .join(AIAnalysis, AIAnalysis.article_id == Article.id)
        .where(AIAnalysis.tags.isnot(None))
    )
    type_q = scope_owner(type_q, Article, user)
    type_rows = await db.execute(type_q)
    for (tags,) in type_rows.all():
        if isinstance(tags, dict):
            pt = tags.get("policy_type")
            if pt:
                type_counts[pt] = type_counts.get(pt, 0) + 1

    return {
        "total": total,
        "analyzed": analyzed,
        "pending": max(0, total - analyzed),
        "recent_7d": recent,
        "by_level": by_level,
        "by_category": by_category,
        "by_policy_type": type_counts,
        "top_sources": top_sources,
    }


async def list_source_names(db: AsyncSession, user: User) -> list[str]:
    q = (
        select(Article.source_name)
        .where(Article.source_name.isnot(None))
        .distinct()
        .order_by(Article.source_name)
    )
    q = scope_owner(q, Article, user)
    result = await db.execute(q)
    return [row[0] for row in result.all() if row[0]]


def _article_filter_query(
    user: User,
    *,
    policy_level: PolicyLevel | None = None,
    project_category: ProjectCategory | None = None,
    source_name: str | None = None,
    has_analysis: bool | None = None,
    policy_type: str | None = None,
    q: str | None = None,
    article_ids: list[int] | None = None,
):
    base = select(Article.id)
    base = scope_owner(base, Article, user)

    if article_ids:
        base = base.where(Article.id.in_(article_ids))
    if policy_level:
        base = base.where(Article.policy_level == policy_level)
    if project_category:
        base = base.where(Article.project_category == project_category)
    if source_name:
        base = base.where(Article.source_name == source_name)
    if has_analysis is False:
        base = base.outerjoin(AIAnalysis, AIAnalysis.article_id == Article.id).where(AIAnalysis.id.is_(None))
    elif has_analysis is True or policy_type:
        base = base.join(AIAnalysis, AIAnalysis.article_id == Article.id)
        if policy_type:
            base = base.where(cast(AIAnalysis.tags, String).ilike(f"%{policy_type}%"))
    if q:
        like = f"%{q}%"
        base = base.where(
            or_(
                Article.title.ilike(like),
                Article.content.ilike(like),
                Article.source_name.ilike(like),
            )
        )
    return base


async def query_article_ids(
    db: AsyncSession,
    user: User,
    *,
    policy_level: PolicyLevel | None = None,
    project_category: ProjectCategory | None = None,
    source_name: str | None = None,
    has_analysis: bool | None = None,
    policy_type: str | None = None,
    q: str | None = None,
    article_ids: list[int] | None = None,
    limit: int = 200,
) -> list[int]:
    base = _article_filter_query(
        user,
        policy_level=policy_level,
        project_category=project_category,
        source_name=source_name,
        has_analysis=has_analysis,
        policy_type=policy_type,
        q=q,
        article_ids=article_ids,
    )
    result = await db.execute(
        base.order_by(*desc_nulls_last(Article.publish_time), Article.created_at.desc()).limit(limit)
    )
    return [row[0] for row in result.all()]
