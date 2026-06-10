import logging

from app.database import async_session_factory
from app.tasks.celery_app import celery_app
from app.utils.async_runner import run_async

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.ai_tasks.analyze_article_task", bind=True, max_retries=2)
def analyze_article_task(
    self, article_id: int, force: bool = False, skip_billing: bool = False
) -> dict:
    async def _analyze():
        async with async_session_factory() as db:
            from app.services.ai_analyze_service import analyze_article_record

            try:
                result = await analyze_article_record(
                    db, article_id, force=force, skip_billing=skip_billing
                )
                await db.commit()
                return result
            except Exception as exc:
                await db.rollback()
                raise exc

    try:
        return run_async(_analyze())
    except Exception as exc:
        logger.exception("AI 分析任务失败 article_id=%s", article_id)
        raise self.retry(exc=exc, countdown=30)
