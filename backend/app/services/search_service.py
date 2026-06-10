try:
    from elasticsearch import AsyncElasticsearch
except ImportError:
    AsyncElasticsearch = None  # type: ignore[misc, assignment]

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.analysis import AIAnalysis
from app.models.article import Article
from app.services.article_service import article_list_item
from app.utils.sql_order import desc_nulls_last

settings = get_settings()


class SearchService:
    def __init__(self) -> None:
        self.es: AsyncElasticsearch | None = None

    async def get_es(self) -> "AsyncElasticsearch | None":
        if AsyncElasticsearch is None:
            return None
        if self.es is None:
            try:
                self.es = AsyncElasticsearch(settings.elasticsearch_url)
                if not await self.es.ping():
                    return None
            except Exception:
                return None
        return self.es

    async def ensure_index(self) -> None:
        es = await self.get_es()
        if not es:
            return
        if not await es.indices.exists(index=settings.elasticsearch_index):
            await es.indices.create(
                index=settings.elasticsearch_index,
                body={
                    "mappings": {
                        "properties": {
                            "title": {"type": "text", "analyzer": "ik_max_word"},
                            "content": {"type": "text", "analyzer": "ik_max_word"},
                            "source_name": {"type": "keyword"},
                            "publish_time": {"type": "date"},
                            "tags": {"type": "object", "enabled": False},
                        }
                    }
                },
            )

    async def index_article(self, article: Article, analysis: AIAnalysis | None = None) -> None:
        es = await self.get_es()
        if not es:
            return
        await self.ensure_index()
        doc = {
            "title": article.title,
            "content": article.content or "",
            "source_name": article.source_name,
            "publish_time": article.publish_time.isoformat() if article.publish_time else None,
            "tags": analysis.tags if analysis else None,
            "keywords": analysis.keywords if analysis else None,
        }
        await es.index(index=settings.elasticsearch_index, id=str(article.id), document=doc)

    async def search(
        self,
        db: AsyncSession,
        query: str,
        skip: int = 0,
        limit: int = 20,
        policy_level=None,
        user=None,
    ) -> tuple[int, list]:
        es = await self.get_es()
        if es:
            try:
                body = {
                    "from": skip,
                    "size": limit,
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "content", "keywords"],
                        }
                    },
                }
                resp = await es.search(index=settings.elasticsearch_index, body=body)
                hits = resp["hits"]["hits"]
                total = resp["hits"]["total"]["value"]
                ids = [int(h["_id"]) for h in hits]
                if not ids:
                    return 0, []

                aq = (
                    select(Article)
                    .options(selectinload(Article.analysis))
                    .where(Article.id.in_(ids))
                )
                if user is not None:
                    from app.services.tenant_scope import scope_owner

                    aq = scope_owner(aq, Article, user)
                result = await db.execute(aq)
                articles = {a.id: a for a in result.scalars().all()}
                items = []
                for aid in ids:
                    a = articles.get(aid)
                    if a:
                        items.append(self._to_list_item(a))
                return total, items
            except Exception:
                pass

        return await self._search_postgres(db, query, skip, limit, policy_level, user)

    async def _search_postgres(
        self, db: AsyncSession, query: str, skip: int, limit: int, policy_level=None, user=None
    ) -> tuple[int, list]:
        pattern = f"%{query}%"
        base = select(Article).options(selectinload(Article.analysis)).where(
            or_(
                Article.title.ilike(pattern),
                Article.content.ilike(pattern),
                Article.source_name.ilike(pattern),
            )
        )
        if user is not None:
            from app.services.tenant_scope import scope_owner

            base = scope_owner(base, Article, user)
        if policy_level:
            base = base.where(Article.policy_level == policy_level)
        count_result = await db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar() or 0

        result = await db.execute(
            base.order_by(*desc_nulls_last(Article.publish_time), Article.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = [article_list_item(a) for a in result.scalars().all()]
        return total, items

    def _to_list_item(self, article: Article):
        return article_list_item(article)


search_service = SearchService()
