import asyncio

from pathlib import Path

import httpx

from app.crawler.parser import extract_list_items

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"

CANDIDATES = [
    "http://www.moe.gov.cn/jyb_xwfb/s5147/",
    "http://www.moe.gov.cn/jyb_xwfb/s271/",
    "http://www.moe.gov.cn/jyb_sy/sy_jyyw/",
    "http://www.moe.gov.cn/jyb_sjzl/s3165/",
]


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "probe_candidates.txt"
    out_path.write_text("", encoding="utf-8")
    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"},
        follow_redirects=True,
        timeout=30,
    ) as client:
        for url in CANDIDATES:
            resp = await client.get(url)
            items = extract_list_items(resp.text, url, None)
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(f"\n=== {url} status={resp.status_code} items={len(items)} ===\n")
                for item in items[:8]:
                    f.write(f"{item['title']}\t{item['url']}\n")
    print("done ->", out_path)


if __name__ == "__main__":
    asyncio.run(main())
