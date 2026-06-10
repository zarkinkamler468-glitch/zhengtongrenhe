import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article
from app.models.subscription import PushChannel, PushLog, SubscribeKeyword
from app.models.user import User
from app.services.push_channels import send_to_channel

logger = logging.getLogger(__name__)


async def match_and_push(db: AsyncSession, article: Article) -> int:
    if not article.id:
        await db.flush()

    text = f"{article.title} {article.content or ''}"
    q = (
        select(SubscribeKeyword)
        .where(SubscribeKeyword.is_active.is_(True))
        .options(selectinload(SubscribeKeyword.user))
    )
    if article.owner_id is not None:
        q = q.where(SubscribeKeyword.user_id == article.owner_id)
    subscriptions = (await db.execute(q)).scalars().all()

    pushed = 0
    for sub in subscriptions:
        if sub.keyword.lower() not in text.lower():
            continue

        exists = await db.execute(
            select(PushLog.id).where(
                PushLog.user_id == sub.user_id,
                PushLog.article_id == article.id,
                PushLog.keyword == sub.keyword,
                PushLog.channel == sub.channel,
            )
        )
        if exists.scalar_one_or_none():
            continue

        success, err = await _send_notification(sub, article)
        db.add(
            PushLog(
                user_id=sub.user_id,
                article_id=article.id,
                keyword=sub.keyword,
                channel=sub.channel,
                status="success" if success else "failed",
                message=article.title if success else (err or "推送失败"),
            )
        )
        if success:
            pushed += 1
    return pushed


async def send_test_push(
    user: User,
    channel: PushChannel,
    channel_config: str | None,
    keyword: str = "测试关键词",
) -> tuple[bool, str | None]:
    return await send_to_channel(
        channel,
        channel_config,
        keyword=keyword,
        title="【测试】教育政策推送通道验证",
        url="https://example.com/policy-test",
        source="系统测试",
        user_email=user.email,
    )


async def _send_notification(sub: SubscribeKeyword, article: Article) -> tuple[bool, str | None]:
    user_email = sub.user.email if sub.user else None
    return await send_to_channel(
        sub.channel,
        sub.channel_config,
        keyword=sub.keyword,
        title=article.title,
        url=article.article_url,
        source=article.source_name,
        user_email=user_email,
    )
