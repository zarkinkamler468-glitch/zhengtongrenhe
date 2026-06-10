import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enum_column import enum_column


class PushChannel(str, enum.Enum):
    WECHAT_WORK = "wechat_work"
    DINGTALK = "dingtalk"
    FEISHU = "feishu"
    EMAIL = "email"
    WECHAT_MP = "wechat_mp"
    WEBHOOK = "webhook"


class SubscribeKeyword(Base):
    __tablename__ = "subscribe_keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    keyword: Mapped[str] = mapped_column(String(128), index=True)
    channel: Mapped[PushChannel] = mapped_column(enum_column(PushChannel), default=PushChannel.EMAIL)
    channel_config: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="keywords")


class PushLog(Base):
    __tablename__ = "push_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), index=True)
    keyword: Mapped[str] = mapped_column(String(128))
    channel: Mapped[PushChannel] = mapped_column(enum_column(PushChannel))
    status: Mapped[str] = mapped_column(String(32))
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


from app.models.user import User  # noqa: E402
