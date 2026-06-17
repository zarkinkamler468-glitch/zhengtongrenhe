from datetime import datetime

from pydantic import BaseModel

from app.models.article import PolicyLevel, ProjectCategory
from app.schemas.analysis import AIAnalysisOut


class AttachmentOut(BaseModel):
    id: int
    file_name: str
    file_url: str
    file_type: str | None
    local_path: str | None

    model_config = {"from_attributes": True}


class ArticleListItem(BaseModel):
    id: int
    title: str
    publish_time: datetime | None
    publisher: str | None
    source_name: str | None
    article_url: str
    policy_level: PolicyLevel
    project_category: ProjectCategory | None
    created_at: datetime
    has_analysis: bool = False
    summary_preview: str | None = None
    policy_type: str | None = None
    keywords: list[str] | None = None

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    total: int
    items: list[ArticleListItem]


class ArticleOverview(BaseModel):
    total: int
    analyzed: int
    pending: int
    recent_7d: int
    by_level: dict[str, int]
    by_category: dict[str, int]
    by_policy_type: dict[str, int]
    top_sources: list[dict[str, int | str]]


class ArticleDetail(BaseModel):
    id: int
    title: str
    content: str | None
    publish_time: datetime | None
    publisher: str | None
    source_name: str | None
    article_url: str
    policy_level: PolicyLevel
    project_category: ProjectCategory | None
    created_at: datetime
    updated_at: datetime
    attachments: list[AttachmentOut] = []
    analysis: AIAnalysisOut | None = None

    model_config = {"from_attributes": True}


class ArticleSearchResult(BaseModel):
    total: int
    items: list[ArticleListItem]
    query: str


class BatchArticleActionBody(BaseModel):
    article_ids: list[int] | None = None
    source_name: str | None = None
    policy_level: PolicyLevel | None = None
    project_category: ProjectCategory | None = None
    policy_type: str | None = None
    q: str | None = None
    limit: int = 200
