"""采集调度：按间隔 / 每日定点 / 仅手动"""
from datetime import date, datetime, time, timedelta, timezone
from typing import Protocol
from zoneinfo import ZoneInfo

from app.models.monitor import CrawlFilterMode, MonitorColumn, ScheduleType
from app.services.crawl_filter import filter_mode_label

TZ = ZoneInfo("Asia/Shanghai")


class ScheduleLike(Protocol):
    auto_crawl_enabled: bool
    schedule_type: ScheduleType
    crawl_interval: int | None
    daily_crawl_time: str | None
    last_crawled_at: datetime | None
    crawl_filter_mode: CrawlFilterMode | None
    filter_keywords: list | None
    filter_date_from: date | None
    filter_date_to: date | None


def _to_local(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ)


def _parse_daily_time(value: str | None) -> time:
    if not value or ":" not in value:
        return time(8, 0)
    parts = value.split(":")
    try:
        return time(int(parts[0]) % 24, int(parts[1]) % 60)
    except ValueError:
        return time(8, 0)


def format_interval(minutes: int) -> str:
    minutes = max(1, minutes)
    if minutes % 60 == 0:
        hours = minutes // 60
        return f"{hours} 小时" if hours > 1 else "1 小时"
    if minutes > 60:
        h, m = divmod(minutes, 60)
        return f"{h} 小时 {m} 分钟"
    return f"{minutes} 分钟"


def schedule_label(column: MonitorColumn) -> str:
    return schedule_label_for_task(column)


def schedule_label_for_task(entity: ScheduleLike) -> str:
    if not entity.auto_crawl_enabled or entity.schedule_type == ScheduleType.MANUAL:
        return "仅手动采集"
    if entity.schedule_type == ScheduleType.DAILY:
        return f"每天 {entity.daily_crawl_time or '08:00'} 自动采集"
    base = f"每 {format_interval(entity.crawl_interval or 30)} 自动采集"
    extra = filter_mode_label(entity)
    if extra != "指定栏目（全量）":
        return f"{base} · {extra}"
    return base


def should_auto_crawl(column: MonitorColumn, now: datetime | None = None) -> bool:
    return should_auto_crawl_task(column, now)


def should_auto_crawl_task(entity: ScheduleLike, now: datetime | None = None) -> bool:
    if not getattr(entity, "is_active", True) or not entity.auto_crawl_enabled:
        return False
    if entity.schedule_type == ScheduleType.MANUAL:
        return False

    now_utc = now or datetime.now(timezone.utc)
    now_local = now_utc.astimezone(TZ)
    last_local = _to_local(entity.last_crawled_at)

    if entity.schedule_type == ScheduleType.INTERVAL:
        interval = timedelta(minutes=entity.crawl_interval or 30)
        if last_local and (now_local - last_local) < interval:
            return False
        return True

    if entity.schedule_type == ScheduleType.DAILY:
        target = _parse_daily_time(entity.daily_crawl_time)
        today_run = datetime.combine(now_local.date(), target, tzinfo=TZ)
        if now_local < today_run:
            return False
        if last_local and last_local >= today_run:
            return False
        return True

    return False
