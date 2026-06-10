from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, UserRoleEnum
from app.schemas.admin import AdminUserOut, SystemSettingsOut, SystemSettingsUpdate, UserQuotaUpdate
from app.services.system_settings_service import (
    get_multi_user_enabled,
    set_multi_user_enabled,
)
from app.utils.deps import require_roles

router = APIRouter()


def _admin_user_out(user: User) -> AdminUserOut:
    return AdminUserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=[r.name for r in user.roles],
        crawl_quota=user.crawl_quota,
        crawl_used=user.crawl_used,
        ai_quota=user.ai_quota,
        ai_used=user.ai_used,
        created_at=user.created_at,
    )


@router.get("/users", response_model=list[AdminUserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN)),
):
    result = await db.execute(
        select(User).options(selectinload(User.roles)).order_by(User.id)
    )
    return [_admin_user_out(u) for u in result.scalars().all()]


@router.patch("/users/{user_id}", response_model=AdminUserOut)
async def update_user_quota(
    user_id: int,
    data: UserQuotaUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN)),
):
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(user, key, val)

    await db.flush()
    return _admin_user_out(user)


@router.get("/settings", response_model=SystemSettingsOut)
async def get_system_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN)),
):
    return SystemSettingsOut(multi_user_enabled=await get_multi_user_enabled(db))


@router.patch("/settings", response_model=SystemSettingsOut)
async def update_system_settings(
    data: SystemSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN)),
):
    enabled = await set_multi_user_enabled(db, data.multi_user_enabled)
    return SystemSettingsOut(multi_user_enabled=enabled)
