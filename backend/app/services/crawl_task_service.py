"""采集任务 CRUD 与调度辅助"""
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.monitor import CrawlFilterMode, CrawlTask, MonitorColumn, ScheduleType, SourceMonitor
from app.models.user import User
from app.schemas.monitor import CrawlTaskCreate, CrawlTaskUpdate
from app.services.crawl_filter import filter_mode_label
from app.services.crawl_scheduler import schedule_label_for_task, should_auto_crawl_task
from app.services.tenant_scope import assert_task_access, is_admin, scope_owner


def _default_task_name(source: SourceMonitor, columns: list[MonitorColumn]) -> str:
    col_part = "、".join(c.column_name for c in columns[:3])
    if len(columns) > 3:
        col_part += f" 等{len(columns)}栏"
    return f"{source.name} · {col_part}"


async def _load_columns(db: AsyncSession, source_id: int, column_ids: list[int]) -> list[MonitorColumn]:
    result = await db.execute(
        select(MonitorColumn).where(
            MonitorColumn.source_id == source_id,
            MonitorColumn.id.in_(column_ids),
        )
    )
    columns = result.scalars().all()
    if len(columns) != len(set(column_ids)):
        raise ValueError("部分栏目不存在或不属于所选网站")
    return columns


def task_out(task: CrawlTask, source: SourceMonitor | None = None, column_names: list[str] | None = None) -> dict:
    src = source or task.source
    return {
        "id": task.id,
        "name": task.name,
        "source_id": task.source_id,
        "source_name": src.name if src else "",
        "source_url": src.url if src else "",
        "column_ids": task.column_ids or [],
        "column_names": column_names or [],
        "schedule_type": task.schedule_type.value,
        "crawl_interval": task.crawl_interval,
        "daily_crawl_time": task.daily_crawl_time,
        "auto_crawl_enabled": task.auto_crawl_enabled,
        "crawl_filter_mode": task.crawl_filter_mode.value,
        "filter_keywords": task.filter_keywords,
        "filter_date_from": task.filter_date_from.isoformat() if task.filter_date_from else None,
        "filter_date_to": task.filter_date_to.isoformat() if task.filter_date_to else None,
        "is_active": task.is_active,
        "schedule_label": schedule_label_for_task(task),
        "filter_label": filter_mode_label(task),
        "last_crawled_at": task.last_crawled_at,
        "created_at": task.created_at,
        "running": task.is_active and task.auto_crawl_enabled and task.schedule_type != ScheduleType.MANUAL,
    }


async def get_task_for_user(db: AsyncSession, task_id: int, user: User) -> CrawlTask:
    result = await db.execute(select(CrawlTask).where(CrawlTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise ValueError("采集任务不存在")
    assert_task_access(user, task)
    return task


async def list_tasks(db: AsyncSession, user: User) -> list[dict]:
    q = select(CrawlTask).options(selectinload(CrawlTask.source)).order_by(CrawlTask.id.desc())
    q = scope_owner(q, CrawlTask, user)
    result = await db.execute(q)
    tasks = result.scalars().all()
    if not tasks:
        return []

    all_col_ids = {cid for t in tasks for cid in (t.column_ids or [])}
    col_result = await db.execute(select(MonitorColumn).where(MonitorColumn.id.in_(all_col_ids)))
    col_map = {c.id: c.column_name for c in col_result.scalars().all()}

    return [
        task_out(
            t,
            column_names=[col_map[cid] for cid in (t.column_ids or []) if cid in col_map],
        )
        for t in tasks
    ]


async def create_task(db: AsyncSession, data: CrawlTaskCreate, owner_id: int) -> dict:
    source_result = await db.execute(select(SourceMonitor).where(SourceMonitor.id == data.source_id))
    source = source_result.scalar_one_or_none()
    if not source:
        raise ValueError("监测源不存在")

    columns = await _load_columns(db, data.source_id, data.column_ids)
    payload = data.model_dump()
    column_ids = list(dict.fromkeys(payload.pop("column_ids")))
    source_id = payload.pop("source_id")
    name = payload.pop("name", None) or _default_task_name(source, columns)

    if payload.get("schedule_type") == ScheduleType.MANUAL:
        payload["auto_crawl_enabled"] = False

    task = CrawlTask(name=name, source_id=source_id, column_ids=column_ids, owner_id=owner_id, **payload)
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task_out(task, source=source, column_names=[c.column_name for c in columns])


async def update_task(db: AsyncSession, task_id: int, data: CrawlTaskUpdate, user: User) -> dict:
    task = await get_task_for_user(db, task_id, user)
    result = await db.execute(
        select(CrawlTask).options(selectinload(CrawlTask.source)).where(CrawlTask.id == task.id)
    )
    task = result.scalar_one()

    payload = data.model_dump(exclude_unset=True)
    if "column_ids" in payload:
        columns = await _load_columns(db, task.source_id, payload["column_ids"])
        payload["column_ids"] = list(dict.fromkeys(payload["column_ids"]))
        col_names = [c.column_name for c in columns]
    else:
        col_names = None

    if payload.get("schedule_type") == ScheduleType.MANUAL:
        payload["auto_crawl_enabled"] = False

    for key, val in payload.items():
        setattr(task, key, val)

    await db.flush()
    if col_names is None and task.column_ids:
        col_result = await db.execute(
            select(MonitorColumn.column_name).where(MonitorColumn.id.in_(task.column_ids))
        )
        col_names = [row[0] for row in col_result.all()]

    return task_out(task, column_names=col_names or [])


async def build_task_out(db: AsyncSession, task: CrawlTask) -> dict:
    """构建任务响应，预加载来源与栏目名，避免异步懒加载错误。"""
    result = await db.execute(
        select(CrawlTask).options(selectinload(CrawlTask.source)).where(CrawlTask.id == task.id)
    )
    loaded = result.scalar_one()
    col_names: list[str] = []
    if loaded.column_ids:
        col_result = await db.execute(
            select(MonitorColumn.column_name).where(MonitorColumn.id.in_(loaded.column_ids))
        )
        col_names = [row[0] for row in col_result.all()]
    return task_out(loaded, column_names=col_names)


async def toggle_task(db: AsyncSession, task_id: int, user: User) -> dict:
    task = await get_task_for_user(db, task_id, user)
    task.is_active = not task.is_active
    await db.flush()
    return await build_task_out(db, task)


async def prune_column_from_tasks(db: AsyncSession, column_id: int) -> int:
    """从采集任务的栏目列表中移除已删除的栏目；无栏目时删除该任务。"""
    result = await db.execute(select(CrawlTask))
    updated = 0
    for task in result.scalars().all():
        ids = task.column_ids or []
        if column_id not in ids:
            continue
        task.column_ids = [cid for cid in ids if cid != column_id]
        if not task.column_ids:
            await db.delete(task)
        updated += 1
    if updated:
        await db.flush()
    return updated


async def delete_task(db: AsyncSession, task_id: int, user: User) -> str:
    task = await get_task_for_user(db, task_id, user)
    name = task.name
    await db.delete(task)
    return name


async def mark_task_crawled(db: AsyncSession, task_id: int) -> None:
    await db.execute(
        update(CrawlTask)
        .where(CrawlTask.id == task_id)
        .values(last_crawled_at=datetime.now(timezone.utc))
    )


async def migrate_legacy_column_schedules(db: AsyncSession) -> dict:
    """将旧版「栏目即任务」的数据迁移为独立采集任务（仅执行一次）。"""
    existing = await db.execute(select(CrawlTask.id).limit(1))
    if existing.scalar_one_or_none():
        return {"migrated": 0, "skipped": True}

    from app.models.user import User as UserModel

    admin_result = await db.execute(select(UserModel.id).where(UserModel.username == "admin"))
    admin_id = admin_result.scalar_one_or_none()

    result = await db.execute(
        select(MonitorColumn)
        .options(selectinload(MonitorColumn.source))
        .where(MonitorColumn.auto_crawl_enabled.is_(True))
    )
    columns = result.scalars().all()
    migrated = 0

    by_source: dict[int, list[MonitorColumn]] = {}
    for col in columns:
        if col.schedule_type == ScheduleType.MANUAL:
            continue
        by_source.setdefault(col.source_id, []).append(col)

    for source_id, cols in by_source.items():
        source = cols[0].source
        if not source:
            continue
        task = CrawlTask(
            name=_default_task_name(source, cols),
            owner_id=admin_id,
            source_id=source_id,
            column_ids=[c.id for c in cols],
            schedule_type=cols[0].schedule_type,
            crawl_interval=cols[0].crawl_interval or 30,
            daily_crawl_time=cols[0].daily_crawl_time or "08:00",
            auto_crawl_enabled=True,
            crawl_filter_mode=cols[0].crawl_filter_mode,
            filter_keywords=cols[0].filter_keywords,
            filter_date_from=cols[0].filter_date_from,
            filter_date_to=cols[0].filter_date_to,
            is_active=cols[0].is_active,
            last_crawled_at=max((c.last_crawled_at for c in cols if c.last_crawled_at), default=None),
        )
        db.add(task)
        migrated += 1
        for col in cols:
            col.auto_crawl_enabled = False
            col.schedule_type = ScheduleType.MANUAL

    return {"migrated": migrated, "skipped": False}
