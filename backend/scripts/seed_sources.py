"""初始化教育部 + 各省教育厅监测源"""
import asyncio

from app.database import async_session_factory
from app.services.seed_service import seed_monitor_sources


async def seed():
    async with async_session_factory() as db:
        result = await seed_monitor_sources(db)
        await db.commit()
        print(f"监测源初始化完成: {result}")


if __name__ == "__main__":
    asyncio.run(seed())
