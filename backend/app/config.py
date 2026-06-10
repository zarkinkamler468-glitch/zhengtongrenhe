from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./data/edu_policy.db"
    redis_url: str = "redis://localhost:6379/0"
    elasticsearch_url: str = "http://localhost:9200"
    celery_eager: bool = True

    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 1440
    algorithm: str = "HS256"

    llm_provider: str = "deepseek"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    embedding_model: str = ""

    attachment_dir: str = "./data/attachments"
    default_crawl_interval_minutes: int = 30

    elasticsearch_index: str = "edu_policy_articles"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    wechat_mp_appid: str = ""
    wechat_mp_secret: str = ""
    wechat_mp_template_id: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
