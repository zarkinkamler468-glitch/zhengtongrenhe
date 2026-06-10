from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRoleEnum


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str | None = None
    role: UserRoleEnum = UserRoleEnum.USER


class PublicSignup(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None
    is_active: bool
    roles: list[UserRoleEnum]
    crawl_quota: int = 50
    crawl_used: int = 0
    ai_quota: int = 20
    ai_used: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthConfigOut(BaseModel):
    multi_user_enabled: bool
    allow_signup: bool
    allow_public_login: bool
