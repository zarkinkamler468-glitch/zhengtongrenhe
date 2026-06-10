from datetime import date, datetime, timezone
from typing import Protocol

from app.models.monitor import CrawlFilterMode, MonitorColumn


class FilterLike(Protocol):
    crawl_filter_mode: CrawlFilterMode | None
    filter_keywords: list | None
    filter_date_from: date | None
    filter_date_to: date | None


def _as_date(dt: datetime | date | None) -> date | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.date()
    return dt


def matches_crawl_filter(
    column: MonitorColumn | FilterLike,
    title: str,
    content: str = "",
    publish_time: datetime | None = None,
) -> bool:
    mode = column.crawl_filter_mode or CrawlFilterMode.COLUMN
    text = f"{title} {content}".lower()

    if mode == CrawlFilterMode.KEYWORD:
        keywords = column.filter_keywords or []
        if not keywords:
            return True
        return any(kw.lower() in text for kw in keywords if kw)

    if mode == CrawlFilterMode.DATE_RANGE:
        if not publish_time:
            return False
        pub = _as_date(publish_time)
        if column.filter_date_from and pub < column.filter_date_from:
            return False
        if column.filter_date_to and pub > column.filter_date_to:
            return False
        return True

    return True


def filter_mode_label(column: MonitorColumn | FilterLike) -> str:
    mode = column.crawl_filter_mode or CrawlFilterMode.COLUMN
    if mode == CrawlFilterMode.KEYWORD:
        kws = column.filter_keywords or []
        return f"关键词: {', '.join(kws[:3])}" if kws else "关键词筛选"
    if mode == CrawlFilterMode.DATE_RANGE:
        f = column.filter_date_from.isoformat() if column.filter_date_from else "不限"
        t = column.filter_date_to.isoformat() if column.filter_date_to else "至今"
        return f"时间: {f} ~ {t}"
    return "指定栏目（全量）"
