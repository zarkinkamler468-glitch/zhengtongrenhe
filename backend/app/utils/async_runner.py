import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

T = TypeVar("T")

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="async-runner")


def run_async(coro) -> T:
    """在 Celery eager 模式（嵌套于 Uvicorn 事件循环）下也能安全执行协程。"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    return _executor.submit(asyncio.run, coro).result()
