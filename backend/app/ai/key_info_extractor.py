"""从政策原文中提取关键时间（截止时间等），用于校验/修正 AI 结果。"""
from __future__ import annotations

import re
from datetime import datetime

_DATE_CN = r"(\d{4})年(\d{1,2})月(\d{1,2})日"
_DATE_ISO = r"(\d{4})-(\d{1,2})-(\d{1,2})"
_DATE_SLASH = r"(\d{4})/(\d{1,2})/(\d{1,2})"
_DATE_ANY = rf"(?:{_DATE_CN}|{_DATE_ISO}|{_DATE_SLASH})"

_PUBLISH_MARKERS = ("发布时间", "发布日期", "印发时间", "印发日期", "成文日期", "发文日期")
_DEADLINE_MARKERS = (
    "截止日期",
    "截止时间",
    "申报截止",
    "报名截止",
    "提交截止",
    "材料截止",
    "邮寄截止",
    "截至",
    "截止至",
    "截止到",
    "请于",
    "须在",
    "前提交",
    "前报送",
    "前截止",
)


def format_date_cn(dt: datetime) -> str:
    return f"{dt.year}年{dt.month}月{dt.day}日"


def parse_flexible_date(text: str) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    for pattern in (_DATE_CN, _DATE_ISO, _DATE_SLASH):
        match = re.search(pattern, text)
        if not match:
            continue
        try:
            y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return datetime(y, m, d)
        except ValueError:
            continue
    return None


def _context(text: str, start: int, end: int, window: int = 36) -> str:
    lo = max(0, start - window)
    hi = min(len(text), end + window)
    return text[lo:hi]


def _is_publish_context(ctx: str) -> bool:
    return any(m in ctx for m in _PUBLISH_MARKERS)


def _deadline_score(ctx: str, dt: datetime, publish_hint: datetime | None) -> int:
    score = 0
    if any(m in ctx for m in _DEADLINE_MARKERS):
        score += 12
    if "前" in ctx and "截止" in ctx:
        score += 8
    if _is_publish_context(ctx):
        score -= 15
    if publish_hint:
        if dt.date() >= publish_hint.date():
            score += 4
        else:
            score -= 8
    return score


def extract_deadline(text: str, publish_hint: datetime | None = None) -> str | None:
    """从原文提取最可能的申报/报名截止时间。"""
    if not text:
        return None

    candidates: list[tuple[int, datetime, str]] = []

    patterns = [
        rf"(?:截止(?:日期|时间)?|截至|申报截止|报名截止|提交截止)[：:\s]*({_DATE_ANY})",
        rf"({_DATE_ANY})\s*(?:24:00|23:59)?\s*前\s*(?:截止|提交|报送|邮寄|申报|报名)",
        rf"({_DATE_ANY})\s*前",
        rf"于\s*({_DATE_ANY})\s*前",
        rf"请在\s*({_DATE_ANY})\s*前",
        rf"须在\s*({_DATE_ANY})\s*前",
        rf"截止[至到：:\s]+({_DATE_ANY})",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            raw = match.group(1)
            dt = parse_flexible_date(raw)
            if not dt:
                continue
            ctx = _context(text, match.start(), match.end())
            score = _deadline_score(ctx, dt, publish_hint)
            if score <= 0:
                continue
            candidates.append((score, dt, format_date_cn(dt)))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][2]


def extract_publish_time(text: str) -> str | None:
    if not text:
        return None
    for pattern in (
        rf"(?:发布时间|发布日期|印发时间)[：:\s]*({_DATE_ANY})",
        rf"({_DATE_ANY})\s*(?:发布|印发)",
    ):
        match = re.search(pattern, text)
        if match:
            dt = parse_flexible_date(match.group(1))
            if dt:
                return format_date_cn(dt)
    return None


def extract_apply_start(text: str) -> str | None:
    if not text:
        return None
    for pattern in (
        rf"(?:申报时间|报名时间|受理时间)[：:\s]*({_DATE_ANY})",
        rf"(?:自|从)\s*({_DATE_ANY})\s*(?:起|开始)",
    ):
        match = re.search(pattern, text)
        if match:
            dt = parse_flexible_date(match.group(1))
            if dt:
                return format_date_cn(dt)
    return None


def _date_in_text(date_str: str | None, text: str) -> bool:
    if not date_str or not text:
        return False
    dt = parse_flexible_date(date_str)
    if not dt:
        return date_str in text
    cn = format_date_cn(dt)
    iso = dt.strftime("%Y-%m-%d")
    slash = f"{dt.year}/{dt.month}/{dt.day}"
    return cn in text or iso in text or slash in text


def refine_key_info(
    content: str,
    key_info: dict | None,
    *,
    publish_hint: datetime | None = None,
) -> dict:
    """用原文规则校验并修正 AI 提取的关键信息。"""
    info = dict(key_info or {})
    text = content or ""

    extracted_deadline = extract_deadline(text, publish_hint)
    extracted_publish = extract_publish_time(text)
    extracted_apply = extract_apply_start(text)

    llm_deadline = info.get("deadline")
    if extracted_deadline:
        if not llm_deadline or not _date_in_text(str(llm_deadline), text):
            info["deadline"] = extracted_deadline
        else:
            llm_dt = parse_flexible_date(str(llm_deadline))
            ext_dt = parse_flexible_date(extracted_deadline)
            if llm_dt and ext_dt and llm_dt != ext_dt:
                # AI 与原文规则不一致时，优先原文高置信提取
                info["deadline"] = extracted_deadline

    if not info.get("publish_time"):
        if extracted_publish:
            info["publish_time"] = extracted_publish
        elif publish_hint:
            info["publish_time"] = format_date_cn(publish_hint)

    if not info.get("apply_start") and extracted_apply:
        info["apply_start"] = extracted_apply

    return info
