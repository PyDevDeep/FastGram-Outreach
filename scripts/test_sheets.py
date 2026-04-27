import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.services.sheets_client import GoogleSheetsClient


async def test_sheets():
    print("🔍 [SHEETS] Перевірка доступу до таблиці...")

    # Виконуємо ініціалізацію та запит без перехоплення помилок
    client = GoogleSheetsClient()
    pending = await client.get_pending_contacts()

    print("✅ [SHEETS] Підключення успішне!")
    print(f"📋 [SHEETS] Знайдено контактів у статусі 'Pending': {len(pending)}")

    if pending:
        first = pending[0]
        print(
            f"👤 [SHEETS] Тестовий лід: {first.get('Instagram Username')} (Рядок: {first.get('_row_index')})"
        )
    else:
        print("⚠️ [SHEETS] У таблиці немає рядків зі статусом 'Pending'. Додай один для тесту.")


if __name__ == "__main__":
    asyncio.run(test_sheets())
