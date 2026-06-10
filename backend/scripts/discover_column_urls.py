"""从各省教育厅首页自动发现通知公告/政策文件栏目 URL。"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.data.monitor_sources_data import MOE_SOURCE, PROVINCIAL_SOURCES

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

NOTICE_KW = ("通知公告", "公告公示", "公示公告", "通知通告", "最新公告", "工作通知", "政务动态")
POLICY_KW = ("政策文件", "政策法规", "规范性文件", "政策解读", "文件库", "政策规章", "其他文件", "政务文件")
SKIP_HREF = ("javascript:", "#", "login", "english", "weibo", "weixin", "gov.cn/")

NOTICE_PATH = re.compile(r"tzgg|gggs|notice|gonggao|xwdt|col\d+", re.I)
POLICY_PATH = re.compile(r"zcfg|zcwj|gfxwj|qtwj|policy|zhengce|col\d+", re.I)


def _score_link(text: str, href: str, base_netloc: str) -> tuple[str, str, int] | None:
    text = text.strip()
    href = href.strip()
    if not text or not href or any(s in href.lower() for s in SKIP_HREF):
        return None
    full = urljoin(f"https://{base_netloc}/", href)
    parsed = urlparse(full)
    if parsed.netloc and base_netloc not in parsed.netloc:
        return None
    if len(text) < 3 or len(text) > 30:
        return None

    for kw in NOTICE_KW:
        if kw in text:
            bonus = 2 if NOTICE_PATH.search(href) else 0
            return ("通知公告", full, 10 + bonus + len(kw))
    for kw in POLICY_KW:
        if kw in text:
            bonus = 2 if POLICY_PATH.search(href) else 0
            return ("政策文件", full, 8 + bonus + len(kw))

    if NOTICE_PATH.search(href) and any(k in text for k in ("公告", "通知")):
        return ("通知公告", full, 6)
    if POLICY_PATH.search(href) and any(k in text for k in ("政策", "文件", "法规")):
        return ("政策文件", full, 6)
    return None


async def discover_source(client: httpx.AsyncClient, src: dict) -> dict:
    base_url = src["url"].rstrip("/") + "/"
    base_netloc = urlparse(base_url).netloc
    found: dict[str, tuple[str, int]] = {}

    try:
        resp = await client.get(base_url)
        if resp.status_code >= 400:
            return {"name": src["name"], "error": f"homepage {resp.status_code}", "columns": {}}
        soup = BeautifulSoup(resp.text, "lxml")
    except Exception as exc:
        return {"name": src["name"], "error": str(exc), "columns": {}}

    for a in soup.select("a[href]"):
        text = a.get_text(" ", strip=True)
        href = a.get("href", "")
        scored = _score_link(text, href, base_netloc)
        if not scored:
            continue
        col_name, full_url, score = scored
        prev = found.get(col_name)
        if not prev or score > prev[1]:
            found[col_name] = (full_url, score)

    # 二级：政务公开页
    zwgk_links = []
    for a in soup.select("a[href]"):
        t = a.get_text(strip=True)
        h = a.get("href", "")
        if any(k in t for k in ("政务公开", "政府信息公开", "公开目录")):
            zwgk_links.append(urljoin(base_url, h))
    for zurl in zwgk_links[:3]:
        try:
            zresp = await client.get(zurl)
            if zresp.status_code >= 400:
                continue
            zsoup = BeautifulSoup(zresp.text, "lxml")
            for a in zsoup.select("a[href]"):
                text = a.get_text(" ", strip=True)
                href = a.get("href", "")
                scored = _score_link(text, href, base_netloc)
                if not scored:
                    continue
                col_name, full_url, score = scored
                prev = found.get(col_name)
                if not prev or score > prev[1]:
                    found[col_name] = (full_url, score + 1)
        except Exception:
            continue

    columns = {k: v[0] for k, v in found.items()}
    return {"name": src["name"], "columns": columns, "error": None}


async def verify_url(client: httpx.AsyncClient, url: str) -> tuple[int, int]:
    """返回 (http_status, list_item_estimate)。"""
    try:
        resp = await client.get(url)
        if resp.status_code >= 400:
            return resp.status_code, 0
        soup = BeautifulSoup(resp.text, "lxml")
        links = soup.select("ul li a, table tr a, .list li a, #list a")
        article_links = [
            a for a in links
            if re.search(r"t20\d{6}|\.html|\.shtml|/col/", a.get("href", ""), re.I)
        ]
        return resp.status_code, len(article_links)
    except Exception:
        return 0, 0


async def main() -> None:
    results = []
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=20) as client:
        for src in [MOE_SOURCE, *PROVINCIAL_SOURCES]:
            disc = await discover_source(client, src)
            verified = {}
            for col_name, url in disc.get("columns", {}).items():
                status, items = await verify_url(client, url)
                verified[col_name] = {"url": url, "status": status, "list_items": items}
            disc["verified"] = verified
            results.append(disc)
            print(json.dumps(disc, ensure_ascii=False))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "discovered_columns.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
