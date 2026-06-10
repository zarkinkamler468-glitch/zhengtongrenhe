from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import Role, User, UserRoleEnum
from app.services.system_settings_service import get_multi_user_enabled, user_is_admin
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效或过期的令牌")

    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")

    if not await get_multi_user_enabled(db) and not user_is_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统已关闭多用户模式，仅管理员可继续使用",
        )
    return user


def require_roles(*roles: UserRoleEnum):
    async def checker(user: User = Depends(get_current_user)) -> User:
        user_roles = {r.name for r in user.roles}
        if not user_roles.intersection(set(roles)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return user

    return checker
