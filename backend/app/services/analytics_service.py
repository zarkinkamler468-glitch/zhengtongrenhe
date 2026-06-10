from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AIAnalysis
from app.models.article import Article
from app.models.user import User
from app.schemas.analytics import AnalyticsOverview, CountStat, HotWordItem, IndustryStat
from app.services.tenant_scope import scope_owner

INDUSTRY_KEYWORDS = {
    "职业教育": "vocational",
    "高等教育": "higher_edu",
    "人工智能教育": "ai_edu",
    "教育数字化": "digital_edu",
}


async def get_analytics_overview(db: AsyncSession, user: User) -> AnalyticsOverview:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    async def count_since(since: datetime | None) -> int:
        q = select(func.count(Article.id))
        q = scope_owner(q, Article, user)
        if since:
            q = q.where(Article.created_at >= since)
        result = await db.execute(q)
        return result.scalar() or 0

    policy_stats = CountStat(
        today=await count_since(today_start),
        this_week=await count_since(week_start),
        this_month=await count_since(month_start),
        total=await count_since(None),
    )

    industry_stats = []
    for name in INDUSTRY_KEYWORDS:
        pattern = f"%{name}%"
        iq = select(func.count(Article.id)).where(
            (Article.title.ilike(pattern)) | (Article.content.ilike(pattern))
        )
        iq = scope_owner(iq, Article, user)
        result = await db.execute(iq)
        industry_stats.append(IndustryStat(name=name, count=result.scalar() or 0))

    kw_q = (
        select(AIAnalysis.keywords)
        .select_from(Article)
        .join(AIAnalysis, AIAnalysis.article_id == Article.id)
        .where(AIAnalysis.keywords.isnot(None))
    )
    kw_q = scope_owner(kw_q, Article, user)
    result = await db.execute(kw_q)
    word_count: dict[str, int] = {}
    for row in result.scalars().all():
        if isinstance(row, list):
            for w in row:
                if isinstance(w, str):
                    word_count[w] = word_count.get(w, 0) + 1

    hot_words = [
        HotWordItem(keyword=k, count=v, trend="up" if v > 3 else "stable")
        for k, v in sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:20]
    ]

    return AnalyticsOverview(
        policy_stats=policy_stats,
        industry_stats=industry_stats,
        hot_words=hot_words,
    )
