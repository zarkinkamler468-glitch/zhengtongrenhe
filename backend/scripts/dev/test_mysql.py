import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

URL = "mysql+aiomysql://edu_policy:111111@127.0.0.1:3306/edu_policy_db?charset=utf8mb4"


async def main() -> None:
    engine = create_async_engine(URL)
    async with engine.connect() as conn:
        value = (await conn.execute(text("SELECT 1"))).scalar()
        print("mysql ok", value)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
