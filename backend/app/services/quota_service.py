"""用户采集与 AI 分析配额"""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.tenant_scope import is_admin


def quota_snapshot(user: User) -> dict:
    return {
        "crawl_quota": user.crawl_quota,
        "crawl_used": user.crawl_used,
        "crawl_remaining": max(0, user.crawl_quota - user.crawl_used),
        "ai_quota": user.ai_quota,
        "ai_used": user.ai_used,
        "ai_remaining": max(0, user.ai_quota - user.ai_used),
    }


def ensure_crawl_quota(user: User) -> None:
    if is_admin(user):
        return
    if user.crawl_used >= user.crawl_quota:
        raise HTTPException(
            status_code=429,
            detail=f"采集次数已用尽（{user.crawl_used}/{user.crawl_quota}），请联系管理员",
        )


def ensure_ai_quota(user: User) -> None:
    if is_admin(user):
        return
    if user.ai_used >= user.ai_quota:
        raise HTTPException(
            status_code=429,
            detail=f"AI 分析次数已用尽（{user.ai_used}/{user.ai_quota}），请联系管理员",
        )


async def consume_crawl(db: AsyncSession, user: User) -> None:
    ensure_crawl_quota(user)
    if not is_admin(user):
        user.crawl_used += 1
        await db.flush()


async def consume_ai(db: AsyncSession, user: User) -> None:
    ensure_ai_quota(user)
    if not is_admin(user):
        user.ai_used += 1
        await db.flush()


async def try_consume_ai(db: AsyncSession, user: User) -> bool:
    """扣减 AI 配额，不足时返回 False（不抛 HTTP 异常，供后台任务使用）。"""
    if is_admin(user):
        return True
    if user.ai_used >= user.ai_quota:
        return False
    user.ai_used += 1
    await db.flush()
    return True
