import asyncio
import re

import httpx

from app.crawler.parser import extract_list_items

CANDIDATES = [
    "http://www.moe.gov.cn/jyb_xwfb/xw_fbh/",
    "http://www.moe.gov.cn/was5/web/search?channelid=239993",
    "http://www.moe.gov.cn/",
]


async def main() -> None:
    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"},
        follow_redirects=True,
        timeout=30,
    ) as client:
        for url in CANDIDATES:
            resp = await client.get(url)
            items = extract_list_items(resp.text, url, None)
            list_links = re.findall(r'href="([^"]+list\.shtml[^"]*)"', resp.text)[:10]
            print("URL", resp.status_code, "items", len(items), url)
            for link in list_links:
                print("  list:", link)
            for item in items[:5]:
                print("  item:", item["title"][:50], "->", item["url"][:80])


if __name__ == "__main__":
    asyncio.run(main())
