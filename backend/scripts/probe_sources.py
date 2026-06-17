"""探测各预设监测源：列表能否解析、详情正文/发布时间是否正常。"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.crawler.fetcher import fetch_html
from app.crawler.parser import extract_article_content, extract_list_items
from app.data.monitor_sources_data import MOE_SOURCE, PROVINCIAL_SOURCES

MIN_CONTENT = 80


async def probe_column(source_name: str, column: dict, *, use_playwright: bool) -> dict:
    url = column["column_url"]
    col_name = column["column_name"]
    list_selector = column.get("list_selector")
    result = {
        "source": source_name,
        "column": col_name,
        "list_url": url,
        "use_playwright": use_playwright,
        "status": "ok",
        "list_items": 0,
        "sample_url": None,
        "content_len": 0,
        "publish_time": None,
        "title": None,
        "error": None,
        "note": None,
    }
    if use_playwright:
        result["status"] = "skip_playwright"
        result["note"] = "需 Playwright，本次未测详情"
        return result

    try:
        list_html = await fetch_html(url, use_playwright=False)
        items = extract_list_items(list_html, url, list_selector)
        result["list_items"] = len(items)
        if not items:
            result["status"] = "list_empty"
            result["note"] = "列表页未解析到文章链接"
            return result

        sample = items[0]
        detail_url = sample["url"]
        result["sample_url"] = detail_url
        detail_html = await fetch_html(detail_url, use_playwright=False)
        parsed = extract_article_content(
            detail_html,
            detail_url,
            title_selector=column.get("title_selector"),
            content_selector=column.get("content_selector"),
            date_selector=column.get("date_selector"),
        )
        content = parsed.get("content") or ""
        result["content_len"] = len(content)
        result["publish_time"] = (
            parsed["publish_time"].isoformat(sep=" ") if parsed.get("publish_time") else None
        )
        result["title"] = (parsed.get("title") or sample.get("title") or "")[:60]

        if len(content) < MIN_CONTENT:
            result["status"] = "content_empty"
            result["note"] = f"正文过短({len(content)}字)，可能选择器不匹配"
        elif not parsed.get("publish_time"):
            result["status"] = "no_publish_time"
            result["note"] = "正文正常但未解析到发布时间"
    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)[:200]

    return result


async def main() -> None:
    tasks: list[tuple[str, dict, bool]] = []
    tasks.append((MOE_SOURCE["name"], MOE_SOURCE["columns"][0], False))
    for src in PROVINCIAL_SOURCES:
        pw = bool(src.get("use_playwright"))
        for col in src["columns"]:
            tasks.append((src["name"], col, pw))

    sem = asyncio.Semaphore(6)

    async def run_one(src_name: str, col: dict, pw: bool) -> dict:
        async with sem:
            return await probe_column(src_name, col, use_playwright=pw)

    results = await asyncio.gather(*(run_one(s, c, p) for s, c, p in tasks))
    out = Path(__file__).resolve().parent / "probe_data.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    by_status: dict[str, list] = {}
    for r in results:
        by_status.setdefault(r["status"], []).append(r)

    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("\n=== SUMMARY ===")
    for status, rows in sorted(by_status.items()):
        print(f"{status}: {len(rows)}")
        for r in rows:
            extra = r.get("note") or r.get("error") or ""
            print(f"  - {r['source']} / {r['column']} | list={r['list_items']} content={r['content_len']} {extra}")


if __name__ == "__main__":
    asyncio.run(main())
