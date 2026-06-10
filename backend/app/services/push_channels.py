import asyncio
import base64
import hashlib
import hmac
import json
import logging
import smtplib
import time
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx

from app.config import get_settings
from app.models.subscription import PushChannel

logger = logging.getLogger(__name__)
settings = get_settings()


def parse_channel_config(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def build_message_text(keyword: str, title: str, url: str, source: str | None) -> str:
    lines = [
        f"【政策预警】匹配关键词：{keyword}",
        f"标题：{title}",
        f"来源：{source or '未知'}",
        f"链接：{url}",
    ]
    return "\n".join(lines)


def build_markdown(keyword: str, title: str, url: str, source: str | None) -> str:
    return (
        f"## 教育政策预警\n\n"
        f"**匹配关键词**：{keyword}\n\n"
        f"**标题**：{title}\n\n"
        f"**来源**：{source or '未知'}\n\n"
        f"**链接**：[查看详情]({url})"
    )


async def send_to_channel(
    channel: PushChannel,
    channel_config: str | None,
    *,
    keyword: str,
    title: str,
    url: str,
    source: str | None,
    user_email: str | None = None,
) -> tuple[bool, str | None]:
    config = parse_channel_config(channel_config)
    text = build_message_text(keyword, title, url, source)
    markdown = build_markdown(keyword, title, url, source)

    try:
        if channel == PushChannel.WEBHOOK:
            return await _send_webhook(config, {"keyword": keyword, "title": title, "url": url, "source": source})

        if channel == PushChannel.EMAIL:
            return await _send_email(config, text, title, user_email)

        if channel == PushChannel.DINGTALK:
            return await _send_dingtalk(config, markdown)

        if channel == PushChannel.FEISHU:
            return await _send_feishu(config, keyword, title, url, source)

        if channel == PushChannel.WECHAT_WORK:
            return await _send_wechat_work(config, markdown)

        if channel == PushChannel.WECHAT_MP:
            return await _send_wechat_mp(config, keyword, title, url)

        return False, f"不支持的渠道: {channel.value}"
    except Exception as exc:
        logger.exception("推送渠道 %s 失败", channel.value)
        return False, str(exc)


async def _send_webhook(config: dict[str, Any], payload: dict[str, Any]) -> tuple[bool, str | None]:
    hook_url = config.get("url")
    if not hook_url:
        return False, "Webhook 未配置 url"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(hook_url, json=payload)
        if resp.is_success:
            return True, None
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"


async def _send_email(
    config: dict[str, Any],
    body: str,
    subject: str,
    user_email: str | None,
) -> tuple[bool, str | None]:
    to_addr = config.get("to") or user_email
    if not to_addr:
        return False, "未配置收件邮箱"
    if not settings.smtp_host:
        logger.info("SMTP 未配置，模拟邮件推送 -> %s: %s", to_addr, subject)
        return True, "SMTP 未配置，已记录（开发模式）"

    def _send() -> None:
        msg = MIMEMultipart()
        msg["From"] = settings.smtp_from or settings.smtp_user
        msg["To"] = to_addr
        msg["Subject"] = f"【政策预警】{subject}"
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(msg["From"], [to_addr], msg.as_string())

    await asyncio.to_thread(_send)
    return True, None


async def _send_dingtalk(config: dict[str, Any], markdown: str) -> tuple[bool, str | None]:
    webhook = config.get("webhook") or config.get("url")
    if not webhook:
        return False, "钉钉未配置 webhook"
    secret = config.get("secret")
    if secret:
        ts = str(round(time.time() * 1000))
        sign_raw = f"{ts}\n{secret}"
        sign = urllib.parse.quote_plus(
            base64.b64encode(hmac.new(secret.encode(), sign_raw.encode(), hashlib.sha256).digest())
        )
        sep = "&" if "?" in webhook else "?"
        webhook = f"{webhook}{sep}timestamp={ts}&sign={sign}"

    payload = {"msgtype": "markdown", "markdown": {"title": "政策预警", "text": markdown}}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(webhook, json=payload)
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.is_success and data.get("errcode", 0) == 0:
            return True, None
        return False, data.get("errmsg") or resp.text[:200]


def _feishu_sign(timestamp: str, secret: str) -> str:
    """飞书自定义机器人签名校验（官方算法）。"""
    string_to_sign = f"{timestamp}\n{secret}"
    return base64.b64encode(
        hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
    ).decode("utf-8")


async def _send_feishu(
    config: dict[str, Any],
    keyword: str,
    title: str,
    url: str,
    source: str | None,
) -> tuple[bool, str | None]:
    webhook = config.get("webhook") or config.get("url")
    if not webhook:
        return False, "飞书未配置 webhook"

    payload: dict[str, Any] = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "教育政策预警",
                    "content": [
                        [
                            {"tag": "text", "text": f"匹配关键词：{keyword}\n"},
                            {"tag": "text", "text": f"标题：{title}\n"},
                            {"tag": "text", "text": f"来源：{source or '未知'}\n"},
                            {"tag": "a", "text": "查看详情", "href": url},
                        ]
                    ],
                }
            }
        },
    }
    secret = config.get("secret")
    if secret:
        ts = str(int(time.time()))
        payload["timestamp"] = ts
        payload["sign"] = _feishu_sign(ts, secret)

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(webhook, json=payload)
        try:
            data = resp.json()
        except Exception:
            data = {}
        if resp.is_success and data.get("code") == 0:
            return True, None
        return False, data.get("msg") or resp.text[:200]


async def _send_wechat_work(config: dict[str, Any], markdown: str) -> tuple[bool, str | None]:
    webhook = config.get("webhook") or config.get("url")
    if not webhook:
        return False, "企业微信未配置 webhook"
    payload = {"msgtype": "markdown", "markdown": {"content": markdown}}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(webhook, json=payload)
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.is_success and data.get("errcode", 0) == 0:
            return True, None
        return False, data.get("errmsg") or resp.text[:200]


async def _send_wechat_mp(
    config: dict[str, Any],
    keyword: str,
    title: str,
    url: str,
) -> tuple[bool, str | None]:
    if not settings.wechat_mp_appid or not settings.wechat_mp_secret:
        return False, "服务端未配置 WECHAT_MP_APPID / WECHAT_MP_SECRET"
    openid = config.get("openid")
    template_id = config.get("template_id") or settings.wechat_mp_template_id
    if not openid or not template_id:
        return False, "微信公众号需配置 openid 与 template_id"

    async with httpx.AsyncClient(timeout=20) as client:
        token_resp = await client.get(
            "https://api.weixin.qq.com/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": settings.wechat_mp_appid,
                "secret": settings.wechat_mp_secret,
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return False, token_data.get("errmsg", "获取 access_token 失败")

        payload = {
            "touser": openid,
            "template_id": template_id,
            "url": url,
            "data": {
                "first": {"value": f"匹配关键词：{keyword}", "color": "#173177"},
                "keyword1": {"value": title[:100]},
                "keyword2": {"value": keyword},
                "remark": {"value": "点击查看政策详情", "color": "#173177"},
            },
        }
        send_resp = await client.post(
            "https://api.weixin.qq.com/cgi-bin/message/template/send",
            params={"access_token": access_token},
            json=payload,
        )
        send_data = send_resp.json()
        if send_data.get("errcode") == 0:
            return True, None
        return False, send_data.get("errmsg", "模板消息发送失败")
