"""监测中心统计与源级汇总"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article
from app.models.monitor import CrawlTask, MonitorColumn, ScheduleType, SourceMonitor, SourceStatus
from app.models.user import CrawlLog, User
from app.services.crawl_scheduler import format_interval, schedule_label_for_task
from app.services.tenant_scope import is_admin, scope_owner

TZ = ZoneInfo("Asia/Shanghai")


def _today_start_utc() -> datetime:
    now_local = datetime.now(TZ)
    start_local = datetime.combine(now_local.date(), datetime.min.time(), tzinfo=TZ)
    return start_local.astimezone(timezone.utc)


async def _article_counts_by_source(db: AsyncSession, user: User) -> dict[int, int]:
    q = (
        select(MonitorColumn.source_id, func.count(Article.id))
        .select_from(MonitorColumn)
        .outerjoin(Article, Article.column_id == MonitorColumn.id)
    )
    if not is_admin(user):
        q = q.where(Article.owner_id == user.id)
    q = q.group_by(MonitorColumn.source_id)
    result = await db.execute(q)
    return {row[0]: row[1] for row in result.all()}


async def _today_articles_by_source(db: AsyncSession, user: User) -> dict[int, int]:
    start = _today_start_utc()
    q = (
        select(MonitorColumn.source_id, func.count(Article.id))
        .select_from(MonitorColumn)
        .join(Article, Article.column_id == MonitorColumn.id)
        .where(Article.created_at >= start)
    )
    if not is_admin(user):
        q = q.where(Article.owner_id == user.id)
    q = q.group_by(MonitorColumn.source_id)
    result = await db.execute(q)
    return {row[0]: row[1] for row in result.all()}


def _tasks_by_source(tasks: list[CrawlTask]) -> dict[int, list[CrawlTask]]:
    grouped: dict[int, list[CrawlTask]] = {}
    for task in tasks:
        grouped.setdefault(task.source_id, []).append(task)
    return grouped


def _source_frequency_label(tasks: list[CrawlTask]) -> str:
    active = [
        t
        for t in tasks
        if t.is_active and t.auto_crawl_enabled and t.schedule_type != ScheduleType.MANUAL
    ]
    if not active:
        return "无自动任务"
    if any(t.schedule_type == ScheduleType.DAILY for t in active):
        daily = next(t for t in active if t.schedule_type == ScheduleType.DAILY)
        return f"每天 {daily.daily_crawl_time or '08:00'}"
    intervals = [t.crawl_interval or 30 for t in active if t.schedule_type == ScheduleType.INTERVAL]
    if intervals:
        return f"每 {format_interval(min(intervals))}"
    return schedule_label_for_task(active[0])


def _source_running(tasks: list[CrawlTask]) -> bool:
    return any(
        t.is_active and t.auto_crawl_enabled and t.schedule_type != ScheduleType.MANUAL for t in tasks
    )


def _source_last_crawled(tasks: list[CrawlTask]) -> datetime | None:
    times = [t.last_crawled_at for t in tasks if t.last_crawled_at]
    return max(times) if times else None


async def get_monitor_stats(db: AsyncSession, user: User) -> dict:
    sources_result = await db.execute(
        select(SourceMonitor).options(selectinload(SourceMonitor.columns))
    )
    sources = sources_result.scalars().all()

    tasks_q = select(CrawlTask)
    tasks_q = scope_owner(tasks_q, CrawlTask, user)
    tasks_result = await db.execute(tasks_q)
    tasks = tasks_result.scalars().all()

    total_columns = sum(len(s.columns) for s in sources)
    active_sources = sum(1 for s in sources if s.status == SourceStatus.ACTIVE)
    running_tasks = sum(
        1
        for t in tasks
        if t.is_active and t.auto_crawl_enabled and t.schedule_type != ScheduleType.MANUAL
    )

    start = _today_start_utc()
    logs_q = select(func.coalesce(func.sum(CrawlLog.new_count), 0)).where(CrawlLog.created_at >= start)
    if not is_admin(user):
        logs_q = logs_q.where(CrawlLog.owner_id == user.id)
    today_logs = await db.execute(logs_q)
    today_from_logs = int(today_logs.scalar() or 0)

    articles_q = select(func.count(Article.id)).where(Article.created_at >= start)
    if not is_admin(user):
        articles_q = articles_q.where(Article.owner_id == user.id)
    today_articles = await db.execute(articles_q)
    today_collected = int(today_articles.scalar() or 0)

    return {
        "active_sources": active_sources,
        "total_sources": len(sources),
        "total_columns": total_columns,
        "total_tasks": len(tasks),
        "running_tasks": running_tasks,
        "today_collected": today_collected or today_from_logs,
    }
