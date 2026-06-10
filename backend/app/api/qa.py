from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.service import ai_service
from app.database import get_db
from app.models.user import User, UserRoleEnum
from app.schemas.analysis import AIQARequest, AIQAResponse
from app.services.search_service import search_service
from app.utils.deps import require_roles

router = APIRouter()


@router.post("/ask", response_model=AIQAResponse)
async def ask_question(
    data: AIQARequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRoleEnum.ADMIN, UserRoleEnum.ANALYST, UserRoleEnum.USER)),
):
    _, items = await search_service.search(db, data.question, skip=0, limit=data.limit, user=user)
    context = []
    for item in items:
        context.append({
            "title": item.title,
            "summary": "",
            "content": item.title,
            "url": item.article_url,
        })

    answer = await ai_service.answer_question(data.question, context)
    related = [
        {"id": i.id, "title": i.title, "url": i.article_url, "source": i.source_name}
        for i in items
    ]
    return AIQAResponse(question=data.question, answer=answer, related_articles=related)
