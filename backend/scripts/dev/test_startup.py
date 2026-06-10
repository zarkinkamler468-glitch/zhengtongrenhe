import asyncio

from fastapi import FastAPI

from app.main import lifespan


async def main() -> None:
    app = FastAPI()
    async with lifespan(app):
        print("startup ok")


if __name__ == "__main__":
    asyncio.run(main())
