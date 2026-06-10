from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.subscription import PushLog, SubscribeKeyword
from app.models.user import User
from app.schemas.subscription import (
    PushLogOut,
    PushTestRequest,
    PushTestResponse,
    SubscribeKeywordCreate,
    SubscribeKeywordOut,
    SubscribeKeywordUpdate,
)
from app.services.push_service import send_test_push
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("", response_model=list[SubscribeKeywordOut])
async def list_subscriptions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SubscribeKeyword)
        .where(SubscribeKeyword.user_id == user.id)
        .order_by(SubscribeKeyword.id.desc())
    )
    return result.scalars().all()


@router.get("/push-logs", response_model=list[PushLogOut])
async def list_push_logs(
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PushLog)
        .where(PushLog.user_id == user.id)
        .order_by(PushLog.id.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("", response_model=SubscribeKeywordOut)
async def create_subscription(
    data: SubscribeKeywordCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = SubscribeKeyword(user_id=user.id, **data.model_dump())
    db.add(sub)
    await db.flush()
    await db.refresh(sub)
    return sub


@router.patch("/{sub_id}", response_model=SubscribeKeywordOut)
async def update_subscription(
    sub_id: int,
    data: SubscribeKeywordUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_user_sub(db, sub_id, user.id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(sub, key, value)
    await db.flush()
    await db.refresh(sub)
    return sub


@router.post("/test", response_model=PushTestResponse)
async def test_push_channel(
    data: PushTestRequest,
    user: User = Depends(get_current_user),
):
    success, err = await send_test_push(user, data.channel, data.channel_config, data.keyword)
    if success:
        return PushTestResponse(success=True, message="测试消息已发送，请检查对应渠道")
    return PushTestResponse(success=False, message=err or "发送失败")


@router.delete("/{sub_id}")
async def delete_subscription(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_user_sub(db, sub_id, user.id)
    await db.delete(sub)
    return {"status": "deleted"}


async def _get_user_sub(db: AsyncSession, sub_id: int, user_id: int) -> SubscribeKeyword:
    result = await db.execute(
        select(SubscribeKeyword).where(
            SubscribeKeyword.id == sub_id,
            SubscribeKeyword.user_id == user_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    return sub
