import logging

import httpx

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


async def fetch_html(url: str, use_playwright: bool = False, timeout: float = 30) -> str:
    if use_playwright:
        return await _fetch_playwright(url, timeout)
    return await _fetch_httpx(url, timeout)


async def _fetch_httpx(url: str, timeout: float) -> str:
    async with httpx.AsyncClient(
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        timeout=timeout,
        verify=False,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        resp.encoding = resp.encoding or "utf-8"
        return resp.text


async def _fetch_playwright(url: str, timeout: float) -> str:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright 未安装，回退到 httpx")
        return await _fetch_httpx(url, timeout)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=int(timeout * 1000))
            html = await page.content()
            return html
        finally:
            await browser.close()


async def download_file(url: str, dest_path: str) -> bool:
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        return True
