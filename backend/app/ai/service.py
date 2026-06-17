import json
import logging
from datetime import datetime

from openai import AsyncOpenAI

from app.ai.key_info_extractor import extract_deadline, refine_key_info
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SUMMARY_PROMPT = """你是教育政策分析专家。请对以下政策/通知原文进行分析，严格以 JSON 格式返回，不要包含 markdown 代码块：

{{
  "summary_100": "100字以内摘要",
  "summary_300": "300字以内摘要",
  "summary_page": "一页纸详细摘要（500-800字）",
  "tags": {{
    "policy_type": "政策类型，如：项目申报/政策文件/通知公告",
    "industry": "行业分类，如：职业教育/高等教育",
    "level": "发布级别：国家级/省级/市级/校级",
    "urgency": "紧急程度：高/中/低"
  }},
  "keywords": ["关键词1", "关键词2"],
  "key_info": {{
    "project_name": "项目名称或null",
    "publish_time": "发布时间或null",
    "apply_start": "申报开始时间或null",
    "deadline": "申报或报名截止时间（勿填公示期/异议期/征求意见期；勿填发布时间/印发日期；原文无则 null，格式如 2025年6月30日）",
    "notice_period": "公示期或异议期（如 2025年6月23日至27日，无则 null）",
    "funding_amount": "资助金额或null",
    "target_audience": "申报对象或null",
    "contact": "联系方式或null",
    "contact_person": "联系人或null"
  }},
  "analysis": {{
    "background": "政策背景",
    "reason": "出台原因",
    "core_content": "核心内容",
    "key_tasks": "重点任务",
    "impact_university": "对高校影响",
    "impact_enterprise": "对企业影响",
    "application_advice": "申报建议"
  }}
}}

原文标题：{title}
原文内容：
{content}
"""

QA_PROMPT = """你是教育政策智能助手。根据以下检索到的政策信息回答用户问题。
如果信息不足，请明确说明。回答使用中文，条理清晰。

用户问题：{question}

相关政策信息：
{context}
"""


class AIService:
    def __init__(self) -> None:
        self.client: AsyncOpenAI | None = None
        if settings.llm_api_key:
            self.client = AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
            )

    async def analyze_article(
        self,
        title: str,
        content: str,
        *,
        publish_time: datetime | None = None,
    ) -> dict:
        if not self.client:
            return self._mock_analysis(title, content, publish_time=publish_time)

        text = (content or title)[:8000]
        prompt = SUMMARY_PROMPT.format(title=title, content=text)

        try:
            resp = await self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            raw = resp.choices[0].message.content or "{}"
            data = json.loads(raw)
            return self._postprocess_analysis(data, text, publish_time=publish_time)
        except Exception as exc:
            logger.exception("AI 分析失败: %s", exc)
            return self._mock_analysis(title, content, publish_time=publish_time)

    def _postprocess_analysis(
        self,
        data: dict,
        content: str,
        *,
        publish_time: datetime | None = None,
    ) -> dict:
        hint = publish_time
        if hint and hint.tzinfo is not None:
            hint = hint.replace(tzinfo=None)
        key_info = refine_key_info(content, data.get("key_info"), publish_hint=hint)
        data["key_info"] = key_info
        return data

    async def get_embedding(self, text: str) -> list[float] | None:
        if not self.client or not settings.embedding_model:
            return None
        try:
            resp = await self.client.embeddings.create(
                model=settings.embedding_model,
                input=text[:4000],
            )
            return resp.data[0].embedding
        except Exception:
            logger.debug("Embedding 不可用（DeepSeek 等模型可跳过）")
            return None

    async def answer_question(self, question: str, context_articles: list[dict]) -> str:
        if not self.client:
            if not context_articles:
                return "未找到相关政策信息，请尝试更换关键词。"
            lines = [f"- {a['title']}: {a.get('summary', '')}" for a in context_articles[:5]]
            return f"根据知识库检索到以下相关政策：\n" + "\n".join(lines)

        context = "\n\n".join(
            f"【{a['title']}】\n摘要：{a.get('summary', '')}\n内容片段：{a.get('content', '')[:500]}"
            for a in context_articles
        )
        prompt = QA_PROMPT.format(question=question, context=context or "无")

        try:
            resp = await self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            logger.exception("AI 问答失败: %s", exc)
            return "AI 服务暂时不可用，请稍后重试。"

    def _mock_analysis(
        self,
        title: str,
        content: str,
        *,
        publish_time: datetime | None = None,
    ) -> dict:
        text = content or title
        short = text[:100] if text else title
        hint = publish_time.replace(tzinfo=None) if publish_time and publish_time.tzinfo else publish_time
        key_info = refine_key_info(
            text,
            {
                "project_name": None,
                "publish_time": None,
                "apply_start": None,
                "deadline": extract_deadline(text, hint),
                "funding_amount": None,
                "target_audience": None,
                "contact": None,
                "contact_person": None,
            },
            publish_hint=hint,
        )
        return {
            "summary_100": short[:100],
            "summary_300": text[:300] if text else title,
            "summary_page": text[:800] if text else title,
            "tags": {
                "policy_type": "通知公告",
                "industry": "教育",
                "level": "未知",
                "urgency": "中",
            },
            "keywords": self._extract_keywords(text or title),
            "key_info": key_info,
            "analysis": {
                "background": "待 AI 模型配置后生成详细解读。",
                "reason": "待分析",
                "core_content": short,
                "key_tasks": "待分析",
                "impact_university": "待分析",
                "impact_enterprise": "待分析",
                "application_advice": "请关注官方通知原文及附件要求。",
            },
        }

    def _extract_keywords(self, text: str) -> list[str]:
        candidates = [
            "职业教育", "高等教育", "产教融合", "双高建设", "人工智能",
            "教育数字化", "实训基地", "项目申报", "科研项目", "教改",
        ]
        return [k for k in candidates if k in text][:8]


ai_service = AIService()
