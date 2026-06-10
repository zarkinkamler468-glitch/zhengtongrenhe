import hashlib
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

DATE_PATTERNS = [
    r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})",
    r"(\d{4})-(\d{2})-(\d{2})",
]


def parse_date(text: str | None) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            try:
                y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
                return datetime(y, m, d)
            except ValueError:
                continue
    return None


def parse_date_from_url(url: str | None) -> datetime | None:
    """从政府站常见路径如 /t20260603_xxx.html 提取发布日期。"""
    if not url:
        return None
    match = re.search(r"[/_.]t(\d{4})(\d{2})(\d{2})", url)
    if not match:
        return None
    try:
        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def resolve_item_date(date_text: str | None, url: str | None = None) -> datetime | None:
    return parse_date(date_text) or parse_date_from_url(url)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


SKIP_URL_PARTS = (
    "en.moe.gov.cn",
    "ru.moe.gov.cn",
    "de.moe.gov.cn",
    "fr.moe.gov.cn",
    "es.moe.gov.cn",
    "ar.moe.gov.cn",
    "ja.moe.gov.cn",
    "zwfw.moe.gov.cn",
    "/login",
    "javascript:",
)

SKIP_TITLE_WORDS = {
    "english", "deutsch", "français", "francais", "español", "espanol", "日本語",
    "联系我们", "网站地图", "网站声明", "无障碍浏览", "个人登录", "微言教育",
}


def _is_valid_list_item(url: str, title: str, base_url: str) -> bool:
    lower_url = url.lower()
    if any(part in lower_url for part in SKIP_URL_PARTS):
        return False
    if len(title.strip()) < 8:
        return False
    if title.strip().lower() in SKIP_TITLE_WORDS:
        return False

    parsed = urlparse(url)
    base = urlparse(base_url)
    if parsed.netloc and base.netloc and parsed.netloc != base.netloc:
        if not parsed.netloc.endswith("moe.gov.cn"):
            return False

    path = parsed.path or ""
    if "moe.gov.cn" in (parsed.netloc or ""):
        if path.endswith("/") and path.count("/") <= 3:
            return False
        if not re.search(r"t20\d+|\.html|\.shtml", path):
            return False
    return True


def _select_list_nodes(soup: BeautifulSoup, list_selector: str | None):
    if list_selector:
        return soup.select(list_selector)
    for selector in ("#list a", ".moe-list a", "ul.list a"):
        nodes = soup.select(selector)
        if nodes:
            return nodes
    return soup.select("ul li a, table tr a, .list li a, .news-list li a")


def extract_list_items(
    html: str,
    base_url: str,
    list_selector: str | None = None,
) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    items: list[dict] = []
    containers = _select_list_nodes(soup, list_selector)

    seen_urls: set[str] = set()
    for el in containers:
        if el.name != "a":
            link = el.find("a")
            if not link:
                continue
            el = link

        href = el.get("href")
        if not href or href.startswith("#") or href.startswith("javascript"):
            continue

        url = urljoin(base_url, href)
        if url in seen_urls:
            continue

        title = el.get_text(strip=True)
        if not _is_valid_list_item(url, title, base_url):
            continue
        seen_urls.add(url)

        parent = el.find_parent("li") or el.find_parent("tr") or el.parent
        date_text = None
        if parent:
            date_el = parent.find(class_=re.compile(r"date|time", re.I))
            if date_el:
                date_text = date_el.get_text(strip=True)
            else:
                date_text = parent.get_text(" ", strip=True)

        resolved_date = resolve_item_date(date_text, url)
        items.append({
            "title": title,
            "url": url,
            "date_text": date_text,
            "publish_time": resolved_date,
        })

    return items[:50]


def extract_article_content(
    html: str,
    url: str,
    title_selector: str | None = None,
    content_selector: str | None = None,
    date_selector: str | None = None,
) -> dict:
    soup = BeautifulSoup(html, "lxml")

    title = ""
    if title_selector:
        el = soup.select_one(title_selector)
        if el:
            title = el.get_text(strip=True)
    if not title:
        for sel in ["h1", ".title", ".article-title", "#title", "title"]:
            el = soup.select_one(sel)
            if el:
                title = el.get_text(strip=True)
                break

    content = ""
    if content_selector:
        el = soup.select_one(content_selector)
        if el:
            content = el.get_text("\n", strip=True)
    if not content:
        for sel in [".content", ".article-content", "#content", ".TRS_Editor", "article"]:
            el = soup.select_one(sel)
            if el:
                content = el.get_text("\n", strip=True)
                break

    publish_time = None
    if date_selector:
        el = soup.select_one(date_selector)
        if el:
            publish_time = parse_date(el.get_text(strip=True))
    if not publish_time:
        for sel in [".date", ".time", ".publish-time", "span[class*='date']"]:
            el = soup.select_one(sel)
            if el:
                publish_time = parse_date(el.get_text(strip=True))
                if publish_time:
                    break

    publisher = None
    for sel in [".source", ".publisher", ".from", "span[class*='source']"]:
        el = soup.select_one(sel)
        if el:
            publisher = el.get_text(strip=True)
            break

    attachments = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        lower = href.lower()
        if any(lower.endswith(ext) for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx"]):
            attachments.append({
                "file_name": a.get_text(strip=True) or href.split("/")[-1],
                "file_url": urljoin(url, href),
                "file_type": lower.rsplit(".", 1)[-1],
            })

    return {
        "title": title,
        "content": content,
        "publish_time": publish_time,
        "publisher": publisher,
        "attachments": attachments,
    }


def is_same_domain(url1: str, url2: str) -> bool:
    return urlparse(url1).netloc == urlparse(url2).netloc
