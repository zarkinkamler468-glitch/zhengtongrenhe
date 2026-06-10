from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRoleEnum
from app.schemas.auth import AuthConfigOut, PublicSignup, Token, UserCreate, UserOut
from app.services.auth_service import authenticate_user, create_user, signup_public
from app.services.quota_service import quota_snapshot
from app.services.system_settings_service import (
    get_multi_user_enabled,
    user_is_admin,
)
from app.utils.deps import get_current_user, require_roles
from app.utils.security import create_access_token

router = APIRouter()


@router.get("/config", response_model=AuthConfigOut)
async def public_auth_config(db: AsyncSession = Depends(get_db)):
    """公开配置：前端据此隐藏注册/登录入口。"""
    enabled = await get_multi_user_enabled(db)
    return AuthConfigOut(
        multi_user_enabled=enabled,
        allow_signup=enabled,
        allow_public_login=enabled,
    )


def _user_out(user: User) -> UserOut:
    return UserOut(
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


@router.post("/signup", response_model=UserOut)
async def signup(data: PublicSignup, db: AsyncSession = Depends(get_db)):
    if not await get_multi_user_enabled(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统已关闭多用户模式，暂不开放注册",
        )
    try:
        user = await signup_public(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _user_out(user)


@router.post("/register", response_model=UserOut)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN)),
):
    try:
        user = await create_user(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _user_out(user)


@router.post("/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已停用")
    if not await get_multi_user_enabled(db) and not user_is_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统已关闭多用户模式，仅管理员可登录",
        )
    token = create_access_token(user.username)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return _user_out(user)


@router.get("/quota")
async def my_quota(user: User = Depends(get_current_user)):
    return quota_snapshot(user)
