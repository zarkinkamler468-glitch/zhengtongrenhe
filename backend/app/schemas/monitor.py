from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models.monitor import (
    ColumnType,
    CrawlFilterMode,
    CrawlInterval,
    ScheduleType,
    SourceStatus,
    SourceType,
)


class SourceMonitorCreate(BaseModel):
    name: str = Field(max_length=128)
    url: str = Field(max_length=512)
    type: SourceType = SourceType.OTHER
    status: SourceStatus = SourceStatus.ACTIVE


class SourceMonitorUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    type: SourceType | None = None
    status: SourceStatus | None = None


class SourceMonitorOut(BaseModel):
    id: int
    name: str
    url: str
    type: SourceType
    status: SourceStatus
    is_preset: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ColumnScheduleUpdate(BaseModel):
    schedule_type: ScheduleType | None = None
    crawl_interval: int | None = Field(None, ge=5, le=10080, description="采集间隔（分钟），最大 168 小时")
    daily_crawl_time: str | None = Field(None, pattern=r"^\d{1,2}:\d{2}$")
    auto_crawl_enabled: bool | None = None
    is_active: bool | None = None

    @field_validator("daily_crawl_time")
    @classmethod
    def validate_time(cls, v: str | None) -> str | None:
        if v is None:
            return v
        h, m = v.split(":")
        if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            raise ValueError("时间格式应为 HH:MM，如 08:30")
        return f"{int(h):02d}:{int(m):02d}"


class MonitorColumnCreate(BaseModel):
    source_id: int
    column_name: str = Field(max_length=128)
    column_url: str = Field(max_length=512)
    column_type: ColumnType = ColumnType.NOTICE
    crawl_interval: CrawlInterval = CrawlInterval.MIN_30
    schedule_type: ScheduleType = ScheduleType.INTERVAL
    daily_crawl_time: str = "08:00"
    auto_crawl_enabled: bool = True
    list_selector: str | None = None
    title_selector: str | None = None
    date_selector: str | None = None
    content_selector: str | None = None
    use_playwright: bool = False


class MonitorColumnUpdate(ColumnScheduleUpdate):
    column_name: str | None = None
    column_url: str | None = None
    column_type: ColumnType | None = None
    list_selector: str | None = None
    title_selector: str | None = None
    date_selector: str | None = None
    content_selector: str | None = None
    use_playwright: bool | None = None


class ColumnHealthOut(BaseModel):
    column_id: int
    source_id: int
    column_name: str
    column_url: str
    status: str
    http_ok: bool
    list_count: int
    message: str


class MonitorColumnOut(BaseModel):
    id: int
    source_id: int
    column_name: str
    column_url: str
    column_type: ColumnType
    crawl_interval: int
    schedule_type: ScheduleType
    daily_crawl_time: str | None
    auto_crawl_enabled: bool
    crawl_filter_mode: CrawlFilterMode = CrawlFilterMode.COLUMN
    filter_keywords: list[str] | None = None
    filter_date_from: date | None = None
    filter_date_to: date | None = None
    is_active: bool
    schedule_label: str = ""
    filter_label: str = ""
    list_selector: str | None
    title_selector: str | None
    date_selector: str | None
    content_selector: str | None
    use_playwright: bool
    last_crawled_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MonitorTreeSource(BaseModel):
    id: int
    name: str
    url: str
    type: SourceType
    status: SourceStatus
    is_preset: bool = False
    columns: list[MonitorColumnOut]
    column_count: int = 0
    task_count: int = 0
    article_count: int = 0
    today_new_count: int = 0
    frequency_label: str = ""
    last_crawled_at: datetime | None = None
    running: bool = False


class MonitorStatsOut(BaseModel):
    active_sources: int
    total_sources: int
    total_columns: int
    total_tasks: int = 0
    running_tasks: int
    today_collected: int


class CrawlLogOut(BaseModel):
    id: int
    column_id: int
    column_name: str | None = None
    source_name: str | None = None
    status: str
    new_count: int
    updated_count: int
    error_message: str | None
    created_at: datetime


class BatchCrawlRequest(BaseModel):
    column_ids: list[int] = Field(min_length=1)

    @field_validator("column_ids")
    @classmethod
    def unique_ids(cls, v: list[int]) -> list[int]:
        return list(dict.fromkeys(v))


class BulkScheduleRequest(BaseModel):
    column_ids: list[int] = Field(min_length=1)
    schedule_type: ScheduleType | None = None
    crawl_interval: int | None = Field(None, ge=5, le=10080, description="采集间隔（分钟），最大 168 小时")
    daily_crawl_time: str | None = Field(None, pattern=r"^\d{1,2}:\d{2}$")
    auto_crawl_enabled: bool | None = None
    is_active: bool | None = None
    crawl_filter_mode: CrawlFilterMode | None = None
    filter_keywords: list[str] | None = None
    filter_date_from: date | None = None
    filter_date_to: date | None = None


class CrawlTaskCreate(BaseModel):
    name: str | None = Field(None, max_length=256)
    source_id: int
    column_ids: list[int] = Field(min_length=1)
    schedule_type: ScheduleType = ScheduleType.INTERVAL
    crawl_interval: int | None = Field(30, ge=5, le=10080)
    daily_crawl_time: str | None = Field("08:00", pattern=r"^\d{1,2}:\d{2}$")
    auto_crawl_enabled: bool = True
    is_active: bool = True
    crawl_filter_mode: CrawlFilterMode = CrawlFilterMode.COLUMN
    filter_keywords: list[str] | None = None
    filter_date_from: date | None = None
    filter_date_to: date | None = None

    @field_validator("column_ids")
    @classmethod
    def unique_column_ids(cls, v: list[int]) -> list[int]:
        return list(dict.fromkeys(v))


class CrawlTaskUpdate(BaseModel):
    name: str | None = Field(None, max_length=256)
    column_ids: list[int] | None = Field(None, min_length=1)
    schedule_type: ScheduleType | None = None
    crawl_interval: int | None = Field(None, ge=5, le=10080)
    daily_crawl_time: str | None = Field(None, pattern=r"^\d{1,2}:\d{2}$")
    auto_crawl_enabled: bool | None = None
    is_active: bool | None = None
    crawl_filter_mode: CrawlFilterMode | None = None
    filter_keywords: list[str] | None = None
    filter_date_from: date | None = None
    filter_date_to: date | None = None


class CrawlTaskOut(BaseModel):
    id: int
    name: str
    source_id: int
    source_name: str = ""
    source_url: str = ""
    column_ids: list[int]
    column_names: list[str] = []
    schedule_type: ScheduleType
    crawl_interval: int
    daily_crawl_time: str | None = None
    auto_crawl_enabled: bool
    crawl_filter_mode: CrawlFilterMode
    filter_keywords: list[str] | None = None
    filter_date_from: date | None = None
    filter_date_to: date | None = None
    is_active: bool
    schedule_label: str = ""
    filter_label: str = ""
    last_crawled_at: datetime | None = None
    created_at: datetime
    running: bool = False
