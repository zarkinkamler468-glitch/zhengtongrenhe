from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), unique=True, index=True)
    summary_100: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_300: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_page: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    key_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    json_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    article: Mapped["Article"] = relationship(back_populates="analysis")


from app.models.article import Article  # noqa: E402
