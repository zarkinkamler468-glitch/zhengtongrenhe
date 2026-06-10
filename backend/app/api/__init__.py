from fastapi import APIRouter

from app.api import admin, analytics, articles, auth, logs, monitor, qa, subscriptions

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理后台"])
api_router.include_router(monitor.router, prefix="/monitor", tags=["监测源管理"])
api_router.include_router(articles.router, prefix="/articles", tags=["政策知识库"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["关键词订阅"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["数据分析"])
api_router.include_router(qa.router, prefix="/qa", tags=["AI问答"])
api_router.include_router(logs.router, prefix="/logs", tags=["日志管理"])
