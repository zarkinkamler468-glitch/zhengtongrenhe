from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "edu_policy",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.crawl_tasks", "app.tasks.ai_tasks"],
)

conf = dict(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
)

if settings.celery_eager:
    conf["task_always_eager"] = True
    # AI 分析失败不应阻断采集主流程
    conf["task_eager_propagates"] = False

celery_app.conf.update(
    **conf,
    beat_schedule={
        "schedule-crawl-every-5-min": {
            "task": "app.tasks.crawl_tasks.schedule_crawl_columns",
            "schedule": crontab(minute="*/5"),
        },
    },
)
