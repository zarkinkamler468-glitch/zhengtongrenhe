"""系统级开关（存数据库，管理后台可改）"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_setting import MULTI_USER_ENABLED_KEY, SystemSetting
from app.models.user import UserRoleEnum


def _parse_bool(raw: str | None, *, default: bool = True) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


async def ensure_default_settings(db: AsyncSession) -> None:
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == MULTI_USER_ENABLED_KEY)
    )
    if result.scalar_one_or_none() is None:
        db.add(SystemSetting(key=MULTI_USER_ENABLED_KEY, value="true"))


async def get_multi_user_enabled(db: AsyncSession) -> bool:
    result = await db.execute(
        select(SystemSetting.value).where(SystemSetting.key == MULTI_USER_ENABLED_KEY)
    )
    return _parse_bool(result.scalar_one_or_none())


async def set_multi_user_enabled(db: AsyncSession, enabled: bool) -> bool:
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == MULTI_USER_ENABLED_KEY)
    )
    row = result.scalar_one_or_none()
    value = "true" if enabled else "false"
    if row is None:
        db.add(SystemSetting(key=MULTI_USER_ENABLED_KEY, value=value))
    else:
        row.value = value
    await db.flush()
    return enabled


def user_is_admin(user) -> bool:
    return UserRoleEnum.ADMIN in {r.name for r in user.roles}
