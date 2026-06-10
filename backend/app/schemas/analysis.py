from datetime import datetime

from pydantic import BaseModel, Field


class AIAnalysisOut(BaseModel):
    id: int
    article_id: int
    summary_100: str | None
    summary_300: str | None
    summary_page: str | None
    tags: dict | None
    keywords: list | None
    key_info: dict | None
    analysis: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AIQARequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)


class AIQAResponse(BaseModel):
    question: str
    answer: str
    related_articles: list[dict]
