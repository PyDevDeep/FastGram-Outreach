import asyncio

from sqlalchemy.dialects.postgresql import insert

from app.database import AsyncSessionLocal
from app.models.lead import Lead
from app.services.sheets_client import GoogleSheetsClient
from app.utils.logger import setup_logger

logger = setup_logger("migration")


async def migrate_data() -> None:
    logger.info("Починаємо міграцію даних з Google Sheets у PostgreSQL...")

    try:
        sheets = GoogleSheetsClient()
        # Тягнемо всіх лідів (ліміт 10000 для запасу)
        contacts = await sheets.get_all_contacts(limit=10000)
    except Exception as e:
        logger.critical(f"Помилка підключення до Google Sheets: {e}")
        return

    if not contacts:
        logger.warning("Google Sheets порожній. Немає чого мігрувати.")
        return

    logger.info(f"Знайдено {len(contacts)} записів. Заливаємо в БД...")

    async with AsyncSessionLocal() as session:
        success_count = 0
        error_count = 0

        for row in contacts:
            username = str(row.get("Instagram Username", "")).strip()
            user_id = str(row.get("Instagram User ID", "")).strip()
            template = str(row.get("Message Template", "")).strip()
            status = str(row.get("Status", "pending")).strip().lower()

            # Поля для трекінгу відповідей
            reply_text = str(row.get("Reply Text", "")).strip() or None
            tag = str(row.get("Tag", "")).strip() or None

            if not user_id or not username:
                logger.warning(f"Пропуск рядка без ID/Username: {row}")
                error_count += 1
                continue

            # Формуємо запит вставки. Використовуємо діалект PostgreSQL для UPSERT
            stmt = insert(Lead).values(
                instagram_username=username,
                instagram_user_id=user_id,
                message_template=template,
                status=status,
                reply_text=reply_text,
                tag=tag,
            )

            # Якщо instagram_user_id вже є в базі — оновлюємо статус і теги (UPSERT)
            stmt = stmt.on_conflict_do_update(
                index_elements=["instagram_user_id"],
                set_={
                    "status": stmt.excluded.status,
                    "reply_text": stmt.excluded.reply_text,
                    "tag": stmt.excluded.tag,
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
