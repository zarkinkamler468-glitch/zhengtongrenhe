from datetime import datetime

from pydantic import BaseModel, Field

from app.models.subscription import PushChannel


class SubscribeKeywordCreate(BaseModel):
    keyword: str = Field(min_length=1, max_length=128)
    channel: PushChannel = PushChannel.EMAIL
    channel_config: str | None = None


class SubscribeKeywordUpdate(BaseModel):
    keyword: str | None = Field(default=None, min_length=1, max_length=128)
    channel: PushChannel | None = None
    channel_config: str | None = None
    is_active: bool | None = None


class SubscribeKeywordOut(BaseModel):
    id: int
    user_id: int
    keyword: str
    channel: PushChannel
    channel_config: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PushTestRequest(BaseModel):
    channel: PushChannel
    channel_config: str | None = None
    keyword: str = "测试关键词"


class PushTestResponse(BaseModel):
    success: bool
    message: str | None = None


class PushLogOut(BaseModel):
    id: int
    article_id: int
    keyword: str
    channel: PushChannel
    status: str
    message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
