"""监测栏目 URL 可达性与列表解析健康检查。"""
from __future__ import annotations

import httpx

from app.crawler.fetcher import fetch_html
from app.crawler.parser import extract_list_items
from app.models.monitor import MonitorColumn


def _status_from(http_ok: bool, list_count: int, error: str | None) -> str:
    if error:
        return "error"
    if not http_ok:
        return "error"
    if list_count > 0:
        return "ok"
    return "empty"


def _message(status: str, list_count: int, error: str | None) -> str:
    if status == "ok":
        return f"可采集，列表约 {list_count} 条"
    if status == "empty":
        return "页面可访问但未解析到文章，可能需配置专用选择器或 Playwright"
    return error or "栏目链接不可访问"


async def check_column_health(column: MonitorColumn) -> dict:
    http_ok = False
    list_count = 0
    error: str | None = None

    try:
        html = await fetch_html(column.column_url, use_playwright=column.use_playwright)
        http_ok = True
        items = extract_list_items(html, column.column_url, column.list_selector)
        list_count = len(items)
    except httpx.HTTPStatusError as exc:
        error = f"HTTP {exc.response.status_code}"
    except Exception as exc:
        error = str(exc)[:200]

    status = _status_from(http_ok, list_count, error)
    return {
        "column_id": column.id,
        "source_id": column.source_id,
        "column_name": column.column_name,
        "column_url": column.column_url,
        "status": status,
        "http_ok": http_ok,
        "list_count": list_count,
        "message": _message(status, list_count, error),
    }


async def check_columns_health(columns: list[MonitorColumn]) -> list[dict]:
    results: list[dict] = []
    for column in columns:
        results.append(await check_column_health(column))
    return results
