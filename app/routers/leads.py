from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import verify_api_key
from app.models.lead import Lead

# Захищаємо роутер твоїм API-ключем
router = APIRouter(prefix="/api/leads", tags=["Dashboard"], dependencies=[Depends(verify_api_key)])


@router.get("/")
async def get_all_leads(
    limit: int = 100, offset: int = 0, session: AsyncSession = Depends(get_db_session)
) -> list[dict[str, Any]]:
    """Отримання списку лідів для таблиці на фронтенді."""
    stmt = select(Lead).order_by(Lead.updated_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    leads = result.scalars().all()

    return [
        {
            "id": lead.id,
            "username": lead.instagram_username,
            "status": lead.status,
            "message": lead.message_template,
            "sent_at": lead.sent_timestamp,
            "tag": lead.tag,
            "reply_text": lead.reply_text,
            "reply_timestamp": lead.reply_timestamp,
        }
        for lead in leads
    ]


@router.get("/stats")
async def get_dashboard_stats(session: AsyncSession = Depends(get_db_session)) -> dict[str, int]:
    """Агрегація статистики для дашборду."""
    stmt = select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
    result = await session.execute(stmt)

    stats = {"pending": 0, "sent": 0, "failed": 0, "replied": 0, "total": 0}
    for status, count in result.all():
        if status in stats:
            stats[status] = count
        stats["total"] += count

    return stats
