import asyncio
from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert

from app.database import AsyncSessionLocal
from app.models.lead import Lead
from app.services.sheets_client import GoogleSheetsClient
from app.utils.logger import setup_logger

logger = setup_logger("migration")


def parse_sheet_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        # Парсимо ISO формат
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        try:
            # Парсимо звичайний формат та робимо його timezone-aware
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        except ValueError as e:
            logger.warning(f"Не вдалося розпарсити дату: {date_str}. Помилка: {e}")
            return None


async def migrate_data() -> None:
    logger.info("Починаємо міграцію даних з Google Sheets у PostgreSQL...")

    try:
        sheets = GoogleSheetsClient()
        contacts = await sheets.get_all_contacts(limit=10000)
    except Exception as e:
        logger.critical(f"Помилка підключення до Google Sheets: {e}")
        return

    if not contacts:
        logger.warning("Google Sheets порожній. Немає чого мігрувати.")
        return

    logger.info(f"Знайдено {len(contacts)} записів. Заливаємо/Оновлюємо в БД...")

    async with AsyncSessionLocal() as session:
        success_count = 0
        error_count = 0

        for row in contacts:
            username = str(row.get("Instagram Username", "")).strip()
            user_id = str(row.get("Instagram User ID", "")).strip()
            template = str(row.get("Message Template", "")).strip()
            status = str(row.get("Status", "pending")).strip().lower()

            reply_text = str(row.get("Reply Text", "")).strip() or None
            tag = str(row.get("Tag", "")).strip() or None

            # ВИТЯГУЄМО ДАТИ
            sent_str = str(row.get("Sent Timestamp", "")).strip()
            reply_str = str(row.get("Reply Timestamp", "")).strip()

            sent_timestamp = parse_sheet_date(sent_str)
            reply_timestamp = parse_sheet_date(reply_str)

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
                sent_timestamp=sent_timestamp,  # <-- ДОДАНО
                reply_timestamp=reply_timestamp,  # <-- ДОДАНО
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
            except Exception as e:
                logger.error(f"Помилка запису ліда {username}: {e}")
                error_count += 1

        await session.commit()
        logger.info(f"Міграція завершена. Успішно: {success_count}. Помилок: {error_count}.")


if __name__ == "__main__":
    asyncio.run(migrate_data())
