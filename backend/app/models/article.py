import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enum_column import enum_column


class PolicyLevel(str, enum.Enum):
    NATIONAL = "national"
    PROVINCIAL = "provincial"
    MUNICIPAL = "municipal"
    SCHOOL = "school"
    UNKNOWN = "unknown"


class ProjectCategory(str, enum.Enum):
    NATIONAL = "national"
    PROVINCIAL = "provincial"
    RESEARCH = "research"
    TEACHING_REFORM = "teaching_reform"
    OTHER = "other"


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_owner_url", "owner_id", "article_url", unique=True, mysql_length={"article_url": 191}),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    column_id: Mapped[int | None] = mapped_column(ForeignKey("monitor_columns.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(512), index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    publish_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    publisher: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    article_url: Mapped[str] = mapped_column(String(1024))
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    policy_level: Mapped[PolicyLevel] = mapped_column(enum_column(PolicyLevel), default=PolicyLevel.UNKNOWN)
    project_category: Mapped[ProjectCategory | None] = mapped_column(enum_column(ProjectCategory), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    attachments: Mapped[list["ArticleAttachment"]] = relationship(back_populates="article", cascade="all, delete-orphan")
    analysis: Mapped["AIAnalysis | None"] = relationship(back_populates="article", uselist=False, cascade="all, delete-orphan")


class ArticleAttachment(Base):
    __tablename__ = "article_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), index=True)
    file_name: Mapped[str] = mapped_column(String(256))
    file_url: Mapped[str] = mapped_column(String(1024))
    file_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    article: Mapped[Article] = relationship(back_populates="attachments")


from app.models.analysis import AIAnalysis  # noqa: E402
