from datetime import UTC, datetime

from sqlalchemy import CursorResult, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead


class LeadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_pending_contacts(self, limit: int = 50) -> list[Lead]:
        """Аналог get_pending_contacts з sheets_client"""
        stmt = select(Lead).where(Lead.status == "pending").limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_contact_status(self, lead_id: int, status: str, timestamp: str) -> bool:
        """Аналог update_contact_status з sheets_client"""
        dt_timestamp = datetime.fromisoformat(timestamp)
        stmt = (
            update(Lead)
            .where(Lead.id == lead_id)
            .values(
                status=status.lower(), sent_timestamp=dt_timestamp, updated_at=datetime.now(UTC)
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def add_reply_data(self, user_id: str, reply_text: str, tag: str, timestamp: str) -> bool:
        """Аналог add_reply_data з sheets_client"""
        dt_timestamp = datetime.fromisoformat(timestamp)
        stmt = (
            update(Lead)
            .where(Lead.instagram_user_id == user_id)
            .values(
                status="replied",
                reply_text=reply_text,
                tag=tag,
                reply_timestamp=dt_timestamp,
                updated_at=datetime.now(UTC),
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()

        # Кастуємо результат до CursorResult для доступу до rowcount
        if isinstance(result, CursorResult):
            return result.rowcount > 0
        return False
