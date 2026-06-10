import enum
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enum_column import enum_column


class SourceType(str, enum.Enum):
    MOE = "moe"
    PROVINCIAL = "provincial"
    UNIVERSITY = "university"
    RESEARCH = "research"
    GOVERNMENT = "government"
    OTHER = "other"


class SourceStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ColumnType(str, enum.Enum):
    NOTICE = "notice"
    POLICY = "policy"
    PROJECT_APPLY = "project_apply"
    RESEARCH = "research"
    PROCUREMENT = "procurement"
    INDUSTRY_EDU = "industry_edu"
    DOUBLE_HIGH = "double_high"
    OTHER = "other"


class CrawlInterval(int, enum.Enum):
    MIN_5 = 5
    MIN_15 = 15
    MIN_30 = 30
    MIN_60 = 60


class ScheduleType(str, enum.Enum):
    INTERVAL = "interval"
    DAILY = "daily"
    MANUAL = "manual"


class CrawlFilterMode(str, enum.Enum):
    COLUMN = "column"
    KEYWORD = "keyword"
    DATE_RANGE = "date_range"


class SourceMonitor(Base):
    __tablename__ = "source_monitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(String(512))
    type: Mapped[SourceType] = mapped_column(enum_column(SourceType), default=SourceType.OTHER)
    status: Mapped[SourceStatus] = mapped_column(enum_column(SourceStatus), default=SourceStatus.ACTIVE)
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    columns: Mapped[list["MonitorColumn"]] = relationship(back_populates="source", cascade="all, delete-orphan")
    crawl_tasks: Mapped[list["CrawlTask"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class MonitorColumn(Base):
    __tablename__ = "monitor_columns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source_monitors.id"), index=True)
    column_name: Mapped[str] = mapped_column(String(128))
    column_url: Mapped[str] = mapped_column(String(512))
    column_type: Mapped[ColumnType] = mapped_column(enum_column(ColumnType), default=ColumnType.NOTICE)
    crawl_interval: Mapped[int] = mapped_column(Integer, default=30)
    schedule_type: Mapped[ScheduleType] = mapped_column(enum_column(ScheduleType), default=ScheduleType.INTERVAL)
    daily_crawl_time: Mapped[str | None] = mapped_column(String(8), nullable=True, default="08:00")
    auto_crawl_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    crawl_filter_mode: Mapped[CrawlFilterMode] = mapped_column(
        enum_column(CrawlFilterMode), default=CrawlFilterMode.COLUMN
    )
    filter_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    filter_date_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    filter_date_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    list_selector: Mapped[str | None] = mapped_column(String(256), nullable=True)
    title_selector: Mapped[str | None] = mapped_column(String(256), nullable=True)
    date_selector: Mapped[str | None] = mapped_column(String(256), nullable=True)
    content_selector: Mapped[str | None] = mapped_column(String(256), nullable=True)
    use_playwright: Mapped[bool] = mapped_column(Boolean, default=False)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped[SourceMonitor] = relationship(back_populates="columns")


class CrawlTask(Base):
    """采集任务：独立于预设网站，可单独创建/删除/启停。"""

    __tablename__ = "crawl_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(256))
    source_id: Mapped[int] = mapped_column(ForeignKey("source_monitors.id"), index=True)
    column_ids: Mapped[list] = mapped_column(JSON, default=list)
    crawl_interval: Mapped[int] = mapped_column(Integer, default=30)
    schedule_type: Mapped[ScheduleType] = mapped_column(enum_column(ScheduleType), default=ScheduleType.INTERVAL)
    daily_crawl_time: Mapped[str | None] = mapped_column(String(8), nullable=True, default="08:00")
    auto_crawl_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    crawl_filter_mode: Mapped[CrawlFilterMode] = mapped_column(
        enum_column(CrawlFilterMode), default=CrawlFilterMode.COLUMN
    )
    filter_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    filter_date_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    filter_date_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped[SourceMonitor] = relationship(back_populates="crawl_tasks")
