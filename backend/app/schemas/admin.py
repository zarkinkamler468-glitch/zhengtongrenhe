from datetime import datetime

from pydantic import BaseModel, Field

from app.models.user import UserRoleEnum


class UserQuotaUpdate(BaseModel):
    crawl_quota: int | None = Field(None, ge=0)
    ai_quota: int | None = Field(None, ge=0)
    crawl_used: int | None = Field(None, ge=0)
    ai_used: int | None = Field(None, ge=0)
    is_active: bool | None = None


class AdminUserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None
    is_active: bool
    roles: list[UserRoleEnum]
    crawl_quota: int
    crawl_used: int
    ai_quota: int
    ai_used: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemSettingsOut(BaseModel):
    multi_user_enabled: bool


class SystemSettingsUpdate(BaseModel):
    multi_user_enabled: bool
