from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import get_sheets_client, verify_api_key
from app.models.lead import Lead
from app.services.sheets_client import GoogleSheetsClient

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


# app/routers/leads.py


def parse_sheet_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        except ValueError:
            return None


@router.post("/sync")
async def sync_leads_from_sheets(
    session: AsyncSession = Depends(get_db_session),
    sheets_client: GoogleSheetsClient = Depends(get_sheets_client),
) -> dict[str, Any]:
    """Синхронізує лідів з Google Sheets у PostgreSQL."""
    contacts = await sheets_client.get_all_contacts(limit=10000)
    if not contacts:
        return {
            "status": "success",
            "synced": 0,
            "errors": 0,
            "message": "No contacts found in sheets",
        }

    success_count = 0
    error_count = 0

    for row in contacts:
        username = str(row.get("Instagram Username", "")).strip()
        user_id = str(row.get("Instagram User ID", "")).strip()
        template = str(row.get("Message Template", "")).strip()
        status = str(row.get("Status", "pending")).strip().lower()

        reply_text = str(row.get("Reply Text", "")).strip() or None
        tag = str(row.get("Tag", "")).strip() or None

        sent_timestamp = parse_sheet_date(str(row.get("Sent Timestamp", "")).strip())
        reply_timestamp = parse_sheet_date(str(row.get("Reply Timestamp", "")).strip())

        if not user_id or not username:
            error_count += 1
            continue

        stmt = insert(Lead).values(
            instagram_username=username,
            instagram_user_id=user_id,
            message_template=template,
            status=status,
            reply_text=reply_text,
            tag=tag,
            sent_timestamp=sent_timestamp,
            reply_timestamp=reply_timestamp,
        )

        # UPSERT: Оновлюємо існуючі записи (включаючи дати)
        stmt = stmt.on_conflict_do_update(
            index_elements=["instagram_user_id"],
            set_={
                "status": stmt.excluded.status,
                "reply_text": stmt.excluded.reply_text,
                "tag": stmt.excluded.tag,
                "sent_timestamp": stmt.excluded.sent_timestamp,
                "reply_timestamp": stmt.excluded.reply_timestamp,
            },
        )

        try:
            await session.execute(stmt)
            success_count += 1
        except Exception:
            error_count += 1

    await session.commit()
    return {"status": "success", "synced": success_count, "errors": error_count}
