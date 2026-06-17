import hashlib
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

DATE_PATTERNS = [
    r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})",
    r"(\d{4})-(\d{2})-(\d{2})",
]

DATETIME_PATTERNS = [
    r"(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})",
    r"(\d{4})-(\d{2})-(\d{2})",
    r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日号]?",
]


def parse_date(text: str | None) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    for pattern in DATETIME_PATTERNS:
        match = re.search(pattern, text)
        if not match:
            continue
        try:
            y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if len(match.groups()) >= 5:
                hh, mm = int(match.group(4)), int(match.group(5))
                return datetime(y, m, d, hh, mm)
            return datetime(y, m, d)
        except ValueError:
            continue
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


def _extract_meta_from_soup(soup: BeautifulSoup) -> tuple[datetime | None, str | None]:
    """从详情页元信息区提取发布时间与来源（含贵州等 TRS 模板）。"""
    publish_time: datetime | None = None
    publisher: str | None = None

    meta_regions: list[str] = []
    for sel in (".ArticleInfo", ".DocTextBox", ".detail-meta", ".meta", ".info"):
        el = soup.select_one(sel)
        if el:
            meta_regions.append(el.get_text(" ", strip=True))

    page_text = " ".join(meta_regions) or soup.get_text(" ", strip=True)

    for pattern in (
        r"发布时间[：:\s]*(\d{4}-\d{2}-\d{2}(?:\s+\d{1,2}:\d{2})?)",
        r"发布日期[：:\s]*(\d{4}-\d{2}-\d{2}(?:\s+\d{1,2}:\d{2})?)",
        r"时间[：:\s]*(\d{4}-\d{2}-\d{2}(?:\s+\d{1,2}:\d{2})?)",
    ):
        match = re.search(pattern, page_text)
        if match:
            publish_time = parse_date(match.group(1))
            if publish_time:
                break

    for script in soup.find_all("script"):
        script_text = script.string or script.get_text() or ""
        match = re.search(r"SourceName\s*=\s*['\"]([^'\"]+)['\"]", script_text)
        if match and match.group(1).strip():
            publisher = match.group(1).strip()
            break

    if not publisher:
        for pattern in (
            r"文章来源[：:\s]*([^\s|【\[]+)",
            r"信息来源[：:\s]*([^\s|【\[]+)",
            r"来源[：:\s]*([^\s|【\[]+)",
        ):
            match = re.search(pattern, page_text)
            if match:
                publisher = match.group(1).strip().strip("：:")
                if publisher and publisher not in {"", "来源"}:
                    break

    if publisher:
        publisher = publisher[:256]

    return publish_time, publisher


def _extract_content(soup: BeautifulSoup, content_selector: str | None) -> str:
    candidates: list[str] = []

    if content_selector:
        el = soup.select_one(content_selector)
        if el:
            candidates.append(el.get_text("\n", strip=True))

    for sel in (
        ".DocHtmlCon",
        "#Zoom",
        ".trs_editor_view",
        ".TRS_UEDITOR",
        ".TRS_Editor",
        ".list_newxq",
        "#gknbxq_box",
        ".zfxxgk_right",
        ".gggs02",
        "#zfgkxx10",
        ".newscontnet",
        ".con_main",
        ".zcwjk-xlcon",
        "#vsb_content",
        ".v_news_content",
        ".pages_content",
        ".Custom_UnionStyle",
        ".view",
        ".news_content",
        ".article-content",
        ".detail-content",
        ".mainContent",
        ".conTxt",
        ".xl_conect",
        ".zw",
        ".content",
        "#content",
        "article",
        ".article",
    ):
        for el in soup.select(sel):
            candidates.append(el.get_text("\n", strip=True))

    candidates = [t for t in candidates if len(t) >= 40]
    if not candidates:
        return ""
    # 优先选长度适中（避免整页导航）；过长时取最短仍 >= 200 字的块
    candidates.sort(key=len)
    for text in candidates:
        if 200 <= len(text) <= 12000:
            return text
    return candidates[-1] if len(candidates[-1]) <= 20000 else candidates[-1][:20000]


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
    if title.strip().lower() in SKIP_TITLE_WORDS:
        return False

    parsed = urlparse(url)
    base = urlparse(base_url)
    if parsed.netloc and base.netloc and parsed.netloc != base.netloc:
        return False

    path = parsed.path or ""
    if len(title.strip()) < 8:
        # 允许无标题链接，后续由详情页标题补全
        if not re.search(r"t20\d+|/article/\d+|\.html|\.shtml", path, re.I):
            return False
    if re.search(r"/col/col\d+/index\.html", path, re.I):
        return False
    if "/article/category/" in lower_url:
        return False
    if "/jgsz/" in lower_url:
        return False
    if re.search(r"/(tzgg|gfxwj|gzhgfxwjsjk)/?$", path, re.I):
        return False

    if "moe.gov.cn" in (parsed.netloc or ""):
        if path.endswith("/") and path.count("/") <= 3:
            return False
        if not re.search(r"t20\d+|\.html|\.shtml", path):
            return False
    return True


def _select_list_nodes(soup: BeautifulSoup, list_selector: str | None):
    if list_selector:
        return soup.select(list_selector)
    for selector in (
        "ul.wzlb a",
        "a[href*='t20']",
        "#list a",
        ".moe-list a",
        "ul.list a",
        ".news_list li a",
        ".xxgk-list li a",
        "div.list li a",
    ):
        nodes = soup.select(selector)
        if len(nodes) >= 3:
            return nodes
    return soup.select("ul li a, table tr a, .list li a, .news-list li a")


def _resolve_link_title(el) -> str:
    title = el.get_text("\n", strip=True)
    if len(title) < 8:
        title = (el.get("title") or "").strip()
    if len(title) < 8:
        parent = el.find_parent("li") or el.find_parent("tr") or el.parent
        if parent:
            content_el = parent.select_one(".list-content, .title, .bt")
            if content_el:
                title = content_el.get_text(strip=True)
    return title


def _extract_link_urls(el, base_url: str) -> list[str]:
    urls: list[str] = []
    href = el.get("href")
    if href and not href.startswith(("#", "javascript:")):
        urls.append(urljoin(base_url, href))

    onclick = el.get("onclick") or ""
    for match in re.finditer(
        r"""['"]((?:https?:)?//[^'"]+|/?[^'"]*t20\d{6}[^'"]*\.html)['"]""",
        onclick,
    ):
        urls.append(urljoin(base_url, match.group(1)))
    return urls


def _append_list_item(
    items: list[dict],
    seen_urls: set[str],
    *,
    url: str,
    title: str,
    date_text: str | None,
    base_url: str,
) -> None:
    if url in seen_urls:
        return
    if not _is_valid_list_item(url, title, base_url):
        return
    seen_urls.add(url)
    resolved_date = resolve_item_date(date_text, url)
    items.append({
        "title": title,
        "url": url,
        "date_text": date_text,
        "publish_time": resolved_date,
    })


def _extract_list_items_from_html(html: str, base_url: str, list_selector: str | None) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    items: list[dict] = []
    seen_urls: set[str] = set()

    containers = _select_list_nodes(soup, list_selector)
    for el in containers:
        link = el if el.name == "a" else el.find("a")
        if not link:
            continue
        title = _resolve_link_title(link)
        parent = link.find_parent("li") or link.find_parent("tr") or link.parent
        date_text = None
        if parent:
            date_el = parent.find(class_=re.compile(r"date|time", re.I))
            date_text = (date_el.get_text(strip=True) if date_el else parent.get_text(" ", strip=True))
        for url in _extract_link_urls(link, base_url):
            _append_list_item(items, seen_urls, url=url, title=title, date_text=date_text, base_url=base_url)

    for el in soup.select("[onclick*='t20'], [onclick*='http'], a[title]"):
        title = _resolve_link_title(el)
        for url in _extract_link_urls(el, base_url):
            parent = el.find_parent("li") or el.find_parent("tr") or el.parent
            date_text = parent.get_text(" ", strip=True) if parent else None
            _append_list_item(items, seen_urls, url=url, title=title, date_text=date_text, base_url=base_url)

    if len(items) < 3:
        for match in re.finditer(
            r"""href\s*=\s*['"]([^'"]*t20\d{6}[^'"]*\.html)['"]""",
            html,
            re.I,
        ):
            url = urljoin(base_url, match.group(1))
            _append_list_item(
                items,
                seen_urls,
                url=url,
                title="",
                date_text=None,
                base_url=base_url,
            )

    if len(items) < 3:
        for match in re.finditer(
            r"""['"]((?:https?:)?//[^'"]*t20\d{6}[^'"]*\.html)['"]""",
            html,
            re.I,
        ):
            url = urljoin(base_url, match.group(1))
            _append_list_item(
                items,
                seen_urls,
                url=url,
                title="",
                date_text=None,
                base_url=base_url,
            )

    # 仅有 URL、标题过短时，尝试从详情页补标题（列表页 onclick 场景）
    enriched: list[dict] = []
    for item in items:
        if len(item["title"]) >= 8:
            enriched.append(item)
            continue
        enriched.append({**item, "title": item["title"] or item["url"].rsplit("/", 1)[-1]})
    return enriched[:50]


def extract_list_items(
    html: str,
    base_url: str,
    list_selector: str | None = None,
) -> list[dict]:
    return _extract_list_items_from_html(html, base_url, list_selector)


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

    content = _extract_content(soup, content_selector)

    meta_publish, meta_publisher = _extract_meta_from_soup(soup)

    publish_time = meta_publish
    if date_selector:
        el = soup.select_one(date_selector)
        if el:
            publish_time = parse_date(el.get_text(strip=True)) or publish_time
    if not publish_time:
        for sel in [".date", ".time", ".publish-time", "span[class*='date']"]:
            el = soup.select_one(sel)
            if el:
                publish_time = parse_date(el.get_text(strip=True))
                if publish_time:
                    break
    if not publish_time:
        publish_time = parse_date_from_url(url)

    publisher = meta_publisher
    if not publisher:
        for sel in [".source", ".publisher", ".from", ".SourceName", "span[class*='source']"]:
            el = soup.select_one(sel)
            if el:
                publisher = el.get_text(strip=True).replace("文章来源：", "").replace("来源：", "").strip()
                if publisher:
                    break
    if publisher:
        publisher = publisher[:256]

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
