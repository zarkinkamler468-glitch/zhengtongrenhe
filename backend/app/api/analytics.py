from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRoleEnum
from app.schemas.analytics import AnalyticsOverview
from app.services.analytics_service import get_analytics_overview
from app.utils.deps import require_roles

router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverview)
async def analytics_overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    return await get_analytics_overview(db, user)
