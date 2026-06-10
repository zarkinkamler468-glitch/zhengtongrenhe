import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session_factory
from app.crawler.engine import crawl_column
from app.models.monitor import CrawlTask
from app.services.crawl_scheduler import should_auto_crawl_task
from app.services.crawl_task_service import mark_task_crawled
from app.tasks.celery_app import celery_app
from app.utils.async_runner import run_async

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.crawl_tasks.crawl_column_task", bind=True, max_retries=2)
def crawl_column_task(
    self, column_id: int, task_id: int | None = None, owner_id: int | None = None
) -> dict:
    async def _crawl():
        async with async_session_factory() as db:
            try:
                filter_ctx = None
                if task_id:
                    result = await db.execute(select(CrawlTask).where(CrawlTask.id == task_id))
                    filter_ctx = result.scalar_one_or_none()
                effective_owner = owner_id
                if filter_ctx and filter_ctx.owner_id:
                    effective_owner = filter_ctx.owner_id
                result = await crawl_column(
                    db, column_id, filter_ctx=filter_ctx, owner_id=effective_owner
                )
                await db.commit()
                return result
            except Exception as exc:
                await db.rollback()
                raise exc

    try:
        return run_async(_crawl())
    except Exception as exc:
        logger.exception("采集失败 column_id=%s task_id=%s", column_id, task_id)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.tasks.crawl_tasks.crawl_job_task", bind=True, max_retries=1)
def crawl_job_task(self, task_id: int) -> dict:
    async def _run():
        async with async_session_factory() as db:
            result = await db.execute(
                select(CrawlTask).options(selectinload(CrawlTask.source)).where(CrawlTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            if not task or not task.is_active:
                return {"status": "skipped", "task_id": task_id, "results": []}

            results = []
            for column_id in task.column_ids or []:
                try:
                    outcome = await crawl_column(db, column_id, filter_ctx=task)
                    results.append({"column_id": column_id, **outcome})
                except Exception as exc:
                    results.append({"column_id": column_id, "status": "failed", "error": str(exc)})

            await mark_task_crawled(db, task_id)
            await db.commit()
            return {"status": "completed", "task_id": task_id, "results": results}

    try:
        return run_async(_run())
    except Exception as exc:
        logger.exception("采集任务执行失败 task_id=%s", task_id)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.tasks.crawl_tasks.crawl_columns_batch_task")
def crawl_columns_batch_task(
    column_ids: list[int], task_id: int | None = None, owner_id: int | None = None
) -> dict:
    results = []
    for column_id in column_ids:
        try:
            results.append({
                "column_id": column_id,
                **crawl_column_task(column_id, task_id=task_id, owner_id=owner_id),
            })
        except Exception as exc:
            results.append({"column_id": column_id, "status": "failed", "error": str(exc)})
    return {"count": len(column_ids), "results": results}


@celery_app.task(name="app.tasks.crawl_tasks.schedule_crawl_columns")
def schedule_crawl_columns() -> dict:
    async def _schedule():
        now = datetime.now(timezone.utc)
        scheduled = 0

        async with async_session_factory() as db:
            result = await db.execute(select(CrawlTask).where(CrawlTask.is_active.is_(True)))
            tasks = result.scalars().all()

            for task in tasks:
                if not should_auto_crawl_task(task, now):
                    continue
                crawl_job_task.delay(task.id)
                scheduled += 1

        return {"scheduled": scheduled}

    return run_async(_schedule())
