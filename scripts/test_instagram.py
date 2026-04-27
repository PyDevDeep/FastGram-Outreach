import asyncio
import sys
from pathlib import Path

# Додаємо корінь проекту до path для коректних імпортів
sys.path.append(str(Path(__file__).parent.parent))

from app.services.instagram_client import InstagramClient


async def test_auth():
    print("🔍 [INSTAGRAM] Запуск тесту авторизації...")
    client = InstagramClient()

    # Виконуємо логін (враховуючи твою логіку з проксі та шифруванням)
    success = await client.login()

    if success:
        print("✅ [INSTAGRAM] Авторизація успішна!")
        is_valid = await client.check_session_valid()
        print(f"📊 [INSTAGRAM] Статус сесії: {'Валідна' if is_valid else 'Невалідна'}")

        # Обов'язково зупиняємо монітор, щоб скрипт завершився
        await client.stop_proxy_monitor()
    else:
        print("❌ [INSTAGRAM] Помилка авторизації. Дивись logs/app.log")


if __name__ == "__main__":
    asyncio.run(test_auth())
