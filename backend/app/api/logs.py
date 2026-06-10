from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.monitor import MonitorColumn
from app.models.user import CrawlLog, OperationLog, User, UserRoleEnum
from app.schemas.monitor import CrawlLogOut
from app.services.tenant_scope import scope_owner
from app.utils.deps import require_roles

router = APIRouter()


@router.get("/crawl", response_model=list[CrawlLogOut])
async def list_crawl_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    q = select(CrawlLog).order_by(CrawlLog.id.desc()).offset(skip).limit(limit)
    q = scope_owner(q, CrawlLog, user)
    result = await db.execute(q)
    logs = result.scalars().all()
    if not logs:
        return []

    column_ids = {l.column_id for l in logs}
    col_result = await db.execute(
        select(MonitorColumn)
        .options(selectinload(MonitorColumn.source))
        .where(MonitorColumn.id.in_(column_ids))
    )
    columns = {c.id: c for c in col_result.scalars().all()}

    return [
        CrawlLogOut(
            id=l.id,
            column_id=l.column_id,
            column_name=columns[l.column_id].column_name if l.column_id in columns else None,
            source_name=columns[l.column_id].source.name if l.column_id in columns and columns[l.column_id].source else None,
            status=l.status,
            new_count=l.new_count,
            updated_count=l.updated_count,
            error_message=l.error_message,
            created_at=l.created_at,
        )
        for l in logs
    ]


@router.get("/operations")
async def list_operation_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRoleEnum.ADMIN)),
):
    result = await db.execute(
        select(OperationLog).order_by(OperationLog.id.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()
