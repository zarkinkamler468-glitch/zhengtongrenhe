import asyncio
import re
from pathlib import Path

import httpx
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"


async def main() -> None:
    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"},
        follow_redirects=True,
        timeout=30,
    ) as client:
        resp = await client.get("http://www.moe.gov.cn/")
        links = sorted(set(re.findall(r'href="([^"]+)"', resp.text)))
        out = []
        for link in links:
            if "list.shtml" in link or "srcsite" in link or "jyb_" in link:
                out.append(link)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / "moe_links.txt"
        out_path.write_text("\n".join(out[:50]), encoding="utf-8")
        print("saved", len(out), "->", out_path)


if __name__ == "__main__":
    asyncio.run(main())
