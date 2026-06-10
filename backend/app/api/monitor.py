import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.article import Article
from app.models.monitor import (
    CrawlFilterMode,
    CrawlTask,
    MonitorColumn,
    ScheduleType,
    SourceMonitor,
    SourceStatus,
)
from app.models.user import CrawlLog, User, UserRoleEnum
from app.schemas.monitor import (
    BatchCrawlRequest,
    BulkScheduleRequest,
    CrawlTaskCreate,
    CrawlTaskOut,
    CrawlTaskUpdate,
    ColumnHealthOut,
    MonitorColumnCreate,
    MonitorColumnOut,
    MonitorColumnUpdate,
    MonitorStatsOut,
    MonitorTreeSource,
    SourceMonitorCreate,
    SourceMonitorOut,
    SourceMonitorUpdate,
)
from app.services.column_health_service import check_columns_health
from app.services.crawl_filter import filter_mode_label
from app.services.crawl_scheduler import schedule_label
from app.services.crawl_task_service import (
    create_task,
    delete_task,
    get_task_for_user,
    list_tasks,
    prune_column_from_tasks,
    toggle_task,
    update_task,
)
from app.services.quota_service import consume_crawl, ensure_crawl_quota
from app.services.tenant_scope import is_admin, scope_owner
from app.services.monitor_stats_service import (
    _article_counts_by_source,
    _source_frequency_label,
    _source_last_crawled,
    _source_running,
    _tasks_by_source,
    _today_articles_by_source,
    get_monitor_stats,
)
from app.services.seed_service import seed_monitor_sources
from app.config import get_settings
from app.crawler.engine import crawl_column
from app.tasks.crawl_tasks import crawl_column_task, crawl_columns_batch_task, crawl_job_task
from app.utils.deps import require_roles

settings = get_settings()

logger = logging.getLogger(__name__)

router = APIRouter()


def _raise_task_error(exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    raise exc


def _column_out(column: MonitorColumn) -> MonitorColumnOut:
    mode = getattr(column, "crawl_filter_mode", None) or CrawlFilterMode.COLUMN
    data = MonitorColumnOut(
        id=column.id,
        source_id=column.source_id,
        column_name=column.column_name,
        column_url=column.column_url,
        column_type=column.column_type,
        crawl_interval=column.crawl_interval or 30,
        schedule_type=getattr(column, "schedule_type", None) or ScheduleType.INTERVAL,
        daily_crawl_time=getattr(column, "daily_crawl_time", None) or "08:00",
        auto_crawl_enabled=getattr(column, "auto_crawl_enabled", True),
        crawl_filter_mode=mode,
        filter_keywords=getattr(column, "filter_keywords", None),
        filter_date_from=getattr(column, "filter_date_from", None),
        filter_date_to=getattr(column, "filter_date_to", None),
        is_active=column.is_active,
        list_selector=column.list_selector,
        title_selector=column.title_selector,
        date_selector=column.date_selector,
        content_selector=column.content_selector,
        use_playwright=column.use_playwright,
        last_crawled_at=column.last_crawled_at,
        created_at=column.created_at,
    )
    return data.model_copy(
        update={
            "schedule_label": schedule_label(column),
            "filter_label": filter_mode_label(column),
        }
    )


async def _build_tree(db: AsyncSession, user: User) -> list[MonitorTreeSource]:
    result = await db.execute(
        select(SourceMonitor)
        .options(selectinload(SourceMonitor.columns))
        .order_by(SourceMonitor.id)
    )
    sources = result.scalars().all()
    tasks_q = scope_owner(select(CrawlTask), CrawlTask, user)
    tasks_result = await db.execute(tasks_q)
    tasks = tasks_result.scalars().all()
    task_map = _tasks_by_source(tasks)
    article_counts = await _article_counts_by_source(db, user)
    today_counts = await _today_articles_by_source(db, user)
    return [
        MonitorTreeSource(
            id=s.id,
            name=s.name,
            url=s.url,
            type=s.type,
            status=s.status,
            is_preset=s.is_preset,
            column_count=len(s.columns),
            task_count=len(task_map.get(s.id, [])),
            article_count=article_counts.get(s.id, 0),
            today_new_count=today_counts.get(s.id, 0),
            frequency_label=_source_frequency_label(task_map.get(s.id, [])),
            last_crawled_at=_source_last_crawled(task_map.get(s.id, [])),
            running=_source_running(task_map.get(s.id, [])),
            columns=[_column_out(c) for c in sorted(s.columns, key=lambda x: x.id)],
        )
        for s in sources
    ]


@router.get("/stats", response_model=MonitorStatsOut)
async def monitor_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    return await get_monitor_stats(db, user)


@router.get("/bootstrap")
async def bootstrap_monitor(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    """返回预设网站、采集任务与统计"""
    tree = await _build_tree(db, user)
    tasks = await list_tasks(db, user)
    stats = await get_monitor_stats(db, user)
    return {"tree": tree, "tasks": tasks, "stats": stats, "total": len(tree)}


@router.post("/seed")
async def seed_sources(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    """手动同步/补全预设网站（不创建采集任务）"""
    result = await seed_monitor_sources(db, allow_create=True)
    tree = await _build_tree(db, user)
    return {"status": "ok", **result, "tree": tree}


@router.get("/tasks", response_model=list[CrawlTaskOut])
async def get_crawl_tasks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    return await list_tasks(db, user)


@router.post("/tasks", response_model=CrawlTaskOut)
async def create_crawl_task(
    data: CrawlTaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    try:
        return await create_task(db, data, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"创建采集任务失败: {exc}") from exc


@router.put("/tasks/{task_id}", response_model=CrawlTaskOut)
async def update_crawl_task(
    task_id: int,
    data: CrawlTaskUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    try:
        return await update_task(db, task_id, data, user)
    except (PermissionError, ValueError) as exc:
        _raise_task_error(exc)


@router.delete("/tasks/{task_id}")
async def remove_crawl_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    try:
        name = await delete_task(db, task_id, user)
    except (PermissionError, ValueError) as exc:
        _raise_task_error(exc)
    return {"status": "deleted", "name": name}


@router.post("/tasks/{task_id}/toggle")
async def toggle_crawl_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    try:
        return await toggle_task(db, task_id, user)
    except (PermissionError, ValueError) as exc:
        _raise_task_error(exc)


async def _run_task_crawl_sync(db: AsyncSession, task: CrawlTask) -> dict:
    from app.crawler.engine import crawl_column as crawl_column_fn
    from app.services.crawl_task_service import mark_task_crawled

    results = []
    for column_id in task.column_ids or []:
        try:
            outcome = await crawl_column_fn(db, column_id, filter_ctx=task)
            results.append({"column_id": column_id, **outcome})
        except Exception as exc:
            logger.exception("栏目 %s 采集异常", column_id)
            results.append({"column_id": column_id, "status": "failed", "error": str(exc)})
    await mark_task_crawled(db, task.id)
    return {
        "status": "completed",
        "crawl_task_id": task.id,
        "results": results,
        "count": len(task.column_ids or []),
    }


async def _run_task_crawl(db: AsyncSession, task: CrawlTask) -> dict:
    if settings.celery_eager:
        return await _run_task_crawl_sync(db, task)

    try:
        job = crawl_job_task.delay(task.id)
        return {
            "status": "scheduled",
            "crawl_task_id": task.id,
            "celery_task_id": job.id,
            "count": len(task.column_ids or []),
        }
    except Exception as exc:
        logger.warning("Celery 不可用，改为本机同步采集 task_id=%s: %s", task.id, exc)
        return await _run_task_crawl_sync(db, task)


@router.post("/tasks/{task_id}/start")
async def start_crawl_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    try:
        task = await get_task_for_user(db, task_id, user)
    except (PermissionError, ValueError) as exc:
        _raise_task_error(exc)

    if not task.column_ids:
        raise HTTPException(status_code=400, detail="任务未配置栏目")

    ensure_crawl_quota(user)
    await consume_crawl(db, user)

    try:
        return await _run_task_crawl(db, task)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("采集任务启动失败 task_id=%s", task_id)
        raise HTTPException(status_code=500, detail=f"采集失败: {exc}") from exc


@router.post("/batch/tasks/pause-all")
async def pause_all_tasks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    try:
        stmt = update(CrawlTask).values(is_active=False)
        if not is_admin(user):
            stmt = stmt.where(CrawlTask.owner_id == user.id)
        result = await db.execute(stmt)
        return {"paused_tasks": int(result.rowcount or 0)}
    except Exception as exc:
        logger.exception("批量暂停采集任务失败")
        raise HTTPException(status_code=500, detail=f"暂停失败: {exc}") from exc


@router.post("/batch/tasks/start-all")
async def start_all_tasks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    tasks_q = scope_owner(select(CrawlTask).where(CrawlTask.is_active.is_(False)), CrawlTask, user)
    result = await db.execute(tasks_q)
    tasks = result.scalars().all()
    for task in tasks:
        task.is_active = True
    return {"started_tasks": len(tasks)}


@router.delete("/batch/tasks/paused")
async def delete_paused_tasks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    tasks_q = scope_owner(select(CrawlTask).where(CrawlTask.is_active.is_(False)), CrawlTask, user)
    result = await db.execute(tasks_q)
    paused = result.scalars().all()
    names = [t.name for t in paused]
    for task in paused:
        await db.delete(task)
    return {"deleted": len(names), "names": names}


@router.get("/tree", response_model=list[MonitorTreeSource])
async def get_monitor_tree(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    return await _build_tree(db, user)


@router.get("/sources", response_model=list[SourceMonitorOut])
async def list_sources(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    result = await db.execute(select(SourceMonitor).order_by(SourceMonitor.id.desc()))
    return result.scalars().all()


@router.post("/sources", response_model=SourceMonitorOut)
async def create_source(
    data: SourceMonitorCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    source = SourceMonitor(**data.model_dump())
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return source


async def _run_batch_crawl(
    db: AsyncSession, column_ids: list[int], user: User, *, owner_id: int | None = None
) -> dict:
    if not column_ids:
        raise HTTPException(status_code=400, detail="没有可采集的栏目")

    if settings.celery_eager:
        results = []
        for column_id in column_ids:
            try:
                outcome = await crawl_column(
                    db, column_id, owner_id=owner_id if owner_id is not None else user.id
                )
                results.append({"column_id": column_id, **outcome})
            except Exception as exc:
                results.append({"column_id": column_id, "status": "failed", "error": str(exc)})
        return {
            "status": "completed",
            "column_ids": column_ids,
            "results": results,
            "count": len(column_ids),
        }

    task = crawl_columns_batch_task.delay(column_ids, owner_id=user.id)
    return {
        "status": "scheduled",
        "task_id": task.id,
        "column_ids": column_ids,
        "count": len(column_ids),
    }


async def _delete_sources(db: AsyncSession, sources: list[SourceMonitor]) -> list[str]:
    """删除监测源前先解除文章对栏目的引用，避免外键约束失败"""
    if not sources:
        return []
    column_ids = [c.id for s in sources for c in s.columns]
    if column_ids:
        await db.execute(delete(CrawlLog).where(CrawlLog.column_id.in_(column_ids)))
        await db.execute(
            update(Article).where(Article.column_id.in_(column_ids)).values(column_id=None)
        )
    names = [s.name for s in sources]
    for source in sources:
        await db.delete(source)
    await db.flush()
    return names


# 批量操作走 /batch/*，避免与 /sources/{source_id} 路径冲突
@router.post("/batch/enable-and-start")
async def enable_all_and_start(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    """一键启用全部监测源并立即开始采集"""
    result = await db.execute(
        select(SourceMonitor).options(selectinload(SourceMonitor.columns))
    )
    sources = result.scalars().all()
    column_ids: list[int] = []

    for source in sources:
        source.status = SourceStatus.ACTIVE
        for col in source.columns:
            col.is_active = True
            if col.schedule_type == ScheduleType.MANUAL:
                col.schedule_type = ScheduleType.INTERVAL
                col.crawl_interval = col.crawl_interval or 30
            col.auto_crawl_enabled = True
            column_ids.append(col.id)

    await db.flush()
    ensure_crawl_quota(user)
    await consume_crawl(db, user)
    crawl_result = await _run_batch_crawl(db, column_ids, user)
    return {
        "enabled_sources": len(sources),
        "enabled_columns": len(column_ids),
        **crawl_result,
    }


@router.post("/batch/pause-all")
async def pause_all_sources(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    """一键暂停全部监测源"""
    result = await db.execute(
        select(SourceMonitor).options(selectinload(SourceMonitor.columns))
    )
    sources = result.scalars().all()
    for source in sources:
        source.status = SourceStatus.INACTIVE
        for col in source.columns:
            col.is_active = False
            col.auto_crawl_enabled = False
    await db.flush()
    return {"paused_sources": len(sources)}


@router.delete("/batch/paused")
async def delete_paused_sources(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    """已废弃：请使用 DELETE /batch/tasks/paused 删除采集任务"""
    raise HTTPException(status_code=410, detail="请使用采集任务接口删除任务，预设网站不可批量删除")


@router.put("/sources/{source_id}", response_model=SourceMonitorOut)
async def update_source(
    source_id: int,
    data: SourceMonitorUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    result = await db.execute(select(SourceMonitor).where(SourceMonitor.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="监测源不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(source, k, v)
    await db.flush()
    await db.refresh(source)
    return source


@router.post("/sources/{source_id}/toggle")
async def toggle_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    result = await db.execute(
        select(SourceMonitor).options(selectinload(SourceMonitor.columns)).where(SourceMonitor.id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="监测源不存在")
    source.status = (
        SourceStatus.INACTIVE if source.status == SourceStatus.ACTIVE else SourceStatus.ACTIVE
    )
    if source.status == SourceStatus.INACTIVE:
        for col in source.columns:
            col.is_active = False
            col.auto_crawl_enabled = False
    else:
        for col in source.columns:
            col.is_active = True
            if col.schedule_type != ScheduleType.MANUAL:
                col.auto_crawl_enabled = True
    tasks_result = await db.execute(select(CrawlTask).where(CrawlTask.source_id == source_id))
    source_tasks = tasks_result.scalars().all()
    return {"status": source.status.value, "running": _source_running(source_tasks)}


@router.post("/sources/{source_id}/crawl")
async def trigger_source_crawl(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    result = await db.execute(
        select(MonitorColumn.id).where(
            MonitorColumn.source_id == source_id,
            MonitorColumn.is_active.is_(True),
        )
    )
    column_ids = [row[0] for row in result.all()]
    if not column_ids:
        raise HTTPException(status_code=400, detail="该监测源没有可采集的栏目")

    ensure_crawl_quota(user)
    await consume_crawl(db, user)
    return await _run_batch_crawl(db, column_ids, user)


@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    result = await db.execute(
        select(SourceMonitor).options(selectinload(SourceMonitor.columns)).where(SourceMonitor.id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="监测源不存在")
    if source.is_preset:
        raise HTTPException(status_code=400, detail="预设网站不可删除，请删除对应的采集任务")
    name = source.name
    await _delete_sources(db, [source])
    return {"status": "deleted", "name": name}


@router.get("/columns/health", response_model=list[ColumnHealthOut])
async def columns_health(
    source_id: int | None = None,
    column_ids: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    """检测栏目 URL 是否可访问、能否解析到文章列表。"""
    q = select(MonitorColumn).order_by(MonitorColumn.id)
    if source_id:
        q = q.where(MonitorColumn.source_id == source_id)
    if column_ids:
        ids = [int(x) for x in column_ids.split(",") if x.strip().isdigit()]
        if ids:
            q = q.where(MonitorColumn.id.in_(ids))
    result = await db.execute(q)
    columns = result.scalars().all()
    return await check_columns_health(columns)


@router.get("/columns", response_model=list[MonitorColumnOut])
async def list_columns(
    source_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    q = select(MonitorColumn).order_by(MonitorColumn.id.desc())
    if source_id:
        q = q.where(MonitorColumn.source_id == source_id)
    result = await db.execute(q)
    return [_column_out(c) for c in result.scalars().all()]


@router.post("/columns", response_model=MonitorColumnOut)
async def create_column(
    data: MonitorColumnCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    result = await db.execute(select(SourceMonitor).where(SourceMonitor.id == data.source_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="所属网站不存在")
    column = MonitorColumn(**data.model_dump())
    db.add(column)
    await db.flush()
    await db.refresh(column)
    return _column_out(column)


@router.put("/columns/{column_id}", response_model=MonitorColumnOut)
async def update_column(
    column_id: int,
    data: MonitorColumnUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    result = await db.execute(select(MonitorColumn).where(MonitorColumn.id == column_id))
    column = result.scalar_one_or_none()
    if not column:
        raise HTTPException(status_code=404, detail="栏目不存在")
    payload = data.model_dump(exclude_unset=True)
    if payload.get("schedule_type") == ScheduleType.MANUAL:
        payload["auto_crawl_enabled"] = False
    for k, v in payload.items():
        setattr(column, k, v)
    await db.flush()
    await db.refresh(column)
    return _column_out(column)


@router.post("/columns/bulk-schedule")
async def bulk_update_schedule(
    data: BulkScheduleRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    result = await db.execute(select(MonitorColumn).where(MonitorColumn.id.in_(data.column_ids)))
    columns = result.scalars().all()
    if not columns:
        raise HTTPException(status_code=404, detail="未找到栏目")

    updates = data.model_dump(exclude_unset=True, exclude={"column_ids"})
    if updates.get("schedule_type") == ScheduleType.MANUAL:
        updates["auto_crawl_enabled"] = False
    mode = updates.get("crawl_filter_mode")
    if mode == CrawlFilterMode.COLUMN:
        updates["filter_keywords"] = None
        updates["filter_date_from"] = None
        updates["filter_date_to"] = None
    elif mode == CrawlFilterMode.KEYWORD:
        updates["filter_date_from"] = None
        updates["filter_date_to"] = None
    elif mode == CrawlFilterMode.DATE_RANGE:
        updates["filter_keywords"] = None

    for col in columns:
        for k, v in updates.items():
            setattr(col, k, v)

    return {"status": "ok", "updated": len(columns)}


@router.delete("/columns/{column_id}")
async def delete_column(
    column_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN)),
):
    result = await db.execute(select(MonitorColumn).where(MonitorColumn.id == column_id))
    column = result.scalar_one_or_none()
    if not column:
        raise HTTPException(status_code=404, detail="栏目不存在")
    pruned = await prune_column_from_tasks(db, column_id)
    await db.delete(column)
    return {"status": "deleted", "tasks_updated": pruned}


@router.post("/columns/{column_id}/toggle-active")
async def toggle_column_active(
    column_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    result = await db.execute(select(MonitorColumn).where(MonitorColumn.id == column_id))
    column = result.scalar_one_or_none()
    if not column:
        raise HTTPException(status_code=404, detail="栏目不存在")
    column.is_active = not column.is_active
    return {"is_active": column.is_active}


@router.post("/columns/{column_id}/toggle-auto")
async def toggle_column_auto(
    column_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST)),
):
    result = await db.execute(select(MonitorColumn).where(MonitorColumn.id == column_id))
    column = result.scalar_one_or_none()
    if not column:
        raise HTTPException(status_code=404, detail="栏目不存在")
    column.auto_crawl_enabled = not column.auto_crawl_enabled
    if column.auto_crawl_enabled and column.schedule_type == ScheduleType.MANUAL:
        column.schedule_type = ScheduleType.INTERVAL
    if not column.auto_crawl_enabled:
        column.schedule_type = ScheduleType.MANUAL
    return {
        "auto_crawl_enabled": column.auto_crawl_enabled,
        "schedule_type": column.schedule_type.value,
        "schedule_label": schedule_label(column),
    }


@router.post("/columns/{column_id}/crawl")
async def trigger_crawl(
    column_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    ensure_crawl_quota(user)
    await consume_crawl(db, user)
    if settings.celery_eager:
        result = await crawl_column(db, column_id, owner_id=user.id)
        return {"status": "completed", "result": result, "column_ids": [column_id]}
    task = crawl_column_task.delay(column_id, owner_id=user.id)
    return {"status": "scheduled", "task_id": task.id, "column_ids": [column_id]}


@router.post("/crawl/batch")
async def trigger_batch_crawl(
    data: BatchCrawlRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    result = await db.execute(
        select(MonitorColumn.id).where(
            MonitorColumn.id.in_(data.column_ids),
            MonitorColumn.is_active.is_(True),
        )
    )
    valid_ids = [row[0] for row in result.all()]
    if not valid_ids:
        raise HTTPException(status_code=400, detail="没有可采集的栏目")
    ensure_crawl_quota(user)
    await consume_crawl(db, user)
    return await _run_batch_crawl(db, valid_ids, user)
