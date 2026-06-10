from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Role, User, UserRole, UserRoleEnum
from app.schemas.auth import PublicSignup, UserCreate
from app.utils.security import hash_password, verify_password


async def ensure_roles(db: AsyncSession) -> None:
    for role in UserRoleEnum:
        result = await db.execute(select(Role).where(Role.name == role))
        if not result.scalar_one_or_none():
            db.add(Role(name=role, description=role.value))


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise ValueError("用户名已存在")

    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise ValueError("邮箱已存在")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()

    role_result = await db.execute(select(Role).where(Role.name == data.role))
    role = role_result.scalar_one()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    await db.flush()

    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user.id)
    )
    return result.scalar_one()


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def signup_public(db: AsyncSession, data: PublicSignup) -> User:
    payload = UserCreate(
        username=data.username,
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        role=UserRoleEnum.USER,
    )
    return await create_user(db, payload)


async def assign_legacy_ownership(db: AsyncSession) -> None:
    """将无归属的历史数据划归管理员账户。"""
    from sqlalchemy import update

    from app.models.article import Article
    from app.models.monitor import CrawlTask
    from app.models.user import CrawlLog

    result = await db.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one_or_none()
    if not admin:
        return

    await db.execute(
        update(CrawlTask).where(CrawlTask.owner_id.is_(None)).values(owner_id=admin.id)
    )
    await db.execute(
        update(Article).where(Article.owner_id.is_(None)).values(owner_id=admin.id)
    )
    await db.execute(
        update(CrawlLog).where(CrawlLog.owner_id.is_(None)).values(owner_id=admin.id)
    )


async def create_default_admin(db: AsyncSession) -> None:
    await ensure_roles(db)
    result = await db.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one_or_none()
    if admin:
        return

    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        full_name="系统管理员",
        crawl_quota=999999,
        ai_quota=999999,
    )
    db.add(user)
    await db.flush()
    role_result = await db.execute(select(Role).where(Role.name == UserRoleEnum.ADMIN))
    role = role_result.scalar_one()
    db.add(UserRole(user_id=user.id, role_id=role.id))
