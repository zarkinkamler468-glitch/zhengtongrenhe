import asyncio

from pathlib import Path

import httpx
from bs4 import BeautifulSoup

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"

URLS = [
    "http://www.moe.gov.cn/jyb_xwfb/s271/",
    "http://www.moe.gov.cn/jyb_sjzl/s3165/",
    "http://www.moe.gov.cn/jyb_xwfb/s5147/",
    "http://www.moe.gov.cn/jyb_xwfb/s5148/",
]


async def main() -> None:
    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"},
        follow_redirects=True,
        timeout=30,
    ) as client:
        lines = []
        for url in URLS:
            resp = await client.get(url)
            soup = BeautifulSoup(resp.text, "lxml")
            ul = soup.select_one("#list, .moe-list, ul.list")
            count = len(ul.select("a")) if ul else 0
            title = soup.title.get_text(strip=True) if soup.title else ""
            lines.append(f"{url}\t{resp.status_code}\t{count}\t{title}")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / "moe_lists.txt"
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print("saved ->", out_path)


if __name__ == "__main__":
    asyncio.run(main())
