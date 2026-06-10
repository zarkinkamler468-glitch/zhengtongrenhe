"""轻量迁移：为已有 SQLite/PostgreSQL 表补充新字段"""
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.config import get_settings

settings = get_settings()

COLUMN_PATCHES = [
    ("source_monitors", "is_preset", "BOOLEAN DEFAULT 0"),
    ("monitor_columns", "schedule_type", "VARCHAR(32) DEFAULT 'interval'"),
    ("monitor_columns", "daily_crawl_time", "VARCHAR(8) DEFAULT '08:00'"),
    ("monitor_columns", "auto_crawl_enabled", "BOOLEAN DEFAULT 1"),
    ("monitor_columns", "crawl_filter_mode", "VARCHAR(32) DEFAULT 'column'"),
    ("monitor_columns", "filter_keywords", "TEXT"),
    ("monitor_columns", "filter_date_from", "DATE"),
    ("monitor_columns", "filter_date_to", "DATE"),
    ("users", "crawl_quota", "INTEGER DEFAULT 50"),
    ("users", "crawl_used", "INTEGER DEFAULT 0"),
    ("users", "ai_quota", "INTEGER DEFAULT 20"),
    ("users", "ai_used", "INTEGER DEFAULT 0"),
    ("articles", "owner_id", "INTEGER"),
    ("crawl_tasks", "owner_id", "INTEGER"),
    ("crawl_logs", "owner_id", "INTEGER"),
]


async def run_migrations(conn: AsyncConnection) -> None:
    def _existing(sync_conn):
        return {t: {c["name"] for c in inspect(sync_conn).get_columns(t)} for t in inspect(sync_conn).get_table_names()}

    tables = await conn.run_sync(_existing)
    url = settings.database_url
    is_sqlite = "sqlite" in url
    is_mysql = "mysql" in url

    for table, col, col_type in COLUMN_PATCHES:
        if table not in tables or col in tables[table]:
            continue
        ddl = f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
        if is_mysql and "BOOLEAN" in col_type:
            ddl = f"ALTER TABLE {table} ADD COLUMN {col} TINYINT(1) DEFAULT 1"
        elif not is_sqlite and "BOOLEAN" in col_type:
            ddl = f"ALTER TABLE {table} ADD COLUMN {col} BOOLEAN DEFAULT TRUE"
        await conn.execute(text(ddl))

    await _migrate_article_url_index(conn, is_sqlite=is_sqlite, is_mysql=is_mysql)


async def _migrate_article_url_index(
    conn: AsyncConnection, *, is_sqlite: bool, is_mysql: bool
) -> None:
    """将文章唯一约束从「全局 URL」改为「owner_id + URL」，支持多用户各采一份。"""

    def _index_names(sync_conn):
        insp = inspect(sync_conn)
        if "articles" not in insp.get_table_names():
            return set()
        return {idx["name"] for idx in insp.get_indexes("articles")}

    names = await conn.run_sync(_index_names)

    if "ix_articles_article_url" in names:
        if is_mysql:
            await conn.execute(text("ALTER TABLE articles DROP INDEX ix_articles_article_url"))
        elif is_sqlite:
            await conn.execute(text("DROP INDEX IF EXISTS ix_articles_article_url"))
        else:
            await conn.execute(text("DROP INDEX IF EXISTS ix_articles_article_url"))

    names = await conn.run_sync(_index_names)
    if "ix_articles_owner_url" in names:
        return

    if is_mysql:
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX ix_articles_owner_url "
                "ON articles (owner_id, article_url(191))"
            )
        )
    elif is_sqlite:
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_articles_owner_url "
                "ON articles (owner_id, article_url)"
            )
        )
    else:
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_articles_owner_url "
                "ON articles (owner_id, article_url)"
            )
        )
