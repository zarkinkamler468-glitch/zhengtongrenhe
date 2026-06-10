import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import api_router
from app.config import get_settings
from app.database import Base, engine
from app.services.auth_service import assign_legacy_ownership, create_default_admin
from app.services.db_migrate import run_migrations
from app.services.system_settings_service import ensure_default_settings
from app.services.crawl_task_service import migrate_legacy_column_schedules
from app.services.seed_service import ensure_preset_sources
from app.database import async_session_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.attachment_dir).mkdir(parents=True, exist_ok=True)
    if "sqlite" in settings.database_url:
        Path("./data").mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        if "postgresql" in settings.database_url:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        await run_migrations(conn)

    async with async_session_factory() as db:
        await create_default_admin(db)
        await ensure_default_settings(db)
        await assign_legacy_ownership(db)
        seed_result = await ensure_preset_sources(db)
        migrate_result = await migrate_legacy_column_schedules(db)
        await assign_legacy_ownership(db)
        await db.commit()
        logger.info("预设网站: %s, 任务迁移: %s", seed_result, migrate_result)

    logger.info("教育政策智能监测平台 API 已启动")
    yield
    await engine.dispose()


app = FastAPI(
    title="教育政策智能监测平台",
    description="自动监测、采集、AI解读教育政策信息的后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理异常 %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "服务器内部错误"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        },
    )


app.include_router(api_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "edu-policy-monitor",
        "api_version": "1.3-tasks",
    }
