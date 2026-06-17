"""监测源种子数据：教育部 + 全国各省教育厅（网址来自 Excel 汇总表）"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.monitor_sources_data import MOE_SOURCE, PROVINCIAL_SOURCES
from app.models.monitor import MonitorColumn, ScheduleType, SourceMonitor

DEFAULT_SELECTORS = {
    "list_selector": "#list a, .moe-list a, ul.list a, ul li a, .news_list li a, .list li a, .xxgk-list li a, table tr a",
    "title_selector": "h1, .title, .article-title, .sp_title",
    "content_selector": ".TRS_Editor, .article-content, .content, #zoom, .zw",
    "date_selector": ".time, .date, .pubtime, .source_time, span[class*='date']",
}

ALL_SOURCES = [MOE_SOURCE, *PROVINCIAL_SOURCES]
EXPECTED_SOURCE_COUNT = len(ALL_SOURCES)
PRESET_NAMES = {s["name"] for s in ALL_SOURCES}


async def seed_monitor_sources(db: AsyncSession, *, allow_create: bool = True) -> dict:
    """同步预设网站（仅站点与栏目定义，不创建采集任务）。"""
    created_sources = 0
    created_columns = 0
    updated_sources = 0
    updated_columns = 0
    skipped_sources = 0

    for src_data in ALL_SOURCES:
        result = await db.execute(
            select(SourceMonitor).where(SourceMonitor.name == src_data["name"])
        )
        source = result.scalar_one_or_none()
        use_playwright = src_data.get("use_playwright", False)

        if not source:
            if not allow_create:
                skipped_sources += 1
                continue
            source = SourceMonitor(
                name=src_data["name"],
                url=src_data["url"],
                type=src_data["type"],
                is_preset=True,
            )
            db.add(source)
            await db.flush()
            created_sources += 1
        else:
            if not source.is_preset:
                source.is_preset = True
            if source.url != src_data["url"]:
                source.url = src_data["url"]
                updated_sources += 1

        for col in src_data["columns"]:
            col_result = await db.execute(
                select(MonitorColumn).where(
                    MonitorColumn.source_id == source.id,
                    MonitorColumn.column_name == col["column_name"],
                )
            )
            existing_col = col_result.scalar_one_or_none()
            if existing_col:
                changed = False
                if existing_col.column_url != col["column_url"]:
                    existing_col.column_url = col["column_url"]
                    changed = True
                if existing_col.use_playwright != use_playwright:
                    existing_col.use_playwright = use_playwright
                    changed = True
                selectors = {**DEFAULT_SELECTORS, **{k: col[k] for k in DEFAULT_SELECTORS if col.get(k)}}
                for key, val in selectors.items():
                    if getattr(existing_col, key) != val:
                        setattr(existing_col, key, val)
                        changed = True
                if changed:
                    updated_columns += 1
                continue
            if not allow_create:
                continue
            dup_url = await db.execute(
                select(MonitorColumn).where(
                    MonitorColumn.source_id == source.id,
                    MonitorColumn.column_url == col["column_url"],
                )
            )
            if dup_url.scalar_one_or_none():
                continue
            db.add(
                MonitorColumn(
                    source_id=source.id,
                    use_playwright=use_playwright,
                    schedule_type=ScheduleType.MANUAL,
                    auto_crawl_enabled=False,
                    is_active=True,
                    **DEFAULT_SELECTORS,
                    **col,
                )
            )
            created_columns += 1

    count_result = await db.execute(select(func.count(SourceMonitor.id)))
    total_sources = count_result.scalar() or 0

    return {
        "created_sources": created_sources,
        "created_columns": created_columns,
        "updated_sources": updated_sources,
        "updated_columns": updated_columns,
        "skipped_sources": skipped_sources,
        "total_sources": total_sources,
        "expected_sources": EXPECTED_SOURCE_COUNT,
    }


async def ensure_preset_sources(db: AsyncSession) -> dict:
    """启动时补全缺失的预设网站（不删除、不自动创建采集任务）。"""
    result = await seed_monitor_sources(db, allow_create=True)
    return {"ensured": True, **result}
