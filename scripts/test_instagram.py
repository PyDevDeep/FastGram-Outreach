import asyncio
import sys
from pathlib import Path

# Додаємо корінь проекту до path для коректних імпортів
sys.path.append(str(Path(__file__).parent.parent))

from instagrapi import Client  # type: ignore[reportMissingTypeStubs]

from app.config import get_settings
from app.services.instagram_client import InstagramClient


async def test_auth():
    print("🔍 [INSTAGRAM] Запуск тесту авторизації...")

    # Ініціалізуємо конфіг
    settings = get_settings()

    # Ініціалізуємо клієнт з новими залежностями (DI)
    client = InstagramClient(settings=settings, client_factory=Client)

    # Виконуємо логін
    print(f"⚙️ Використовуємо проксі: {settings.proxy_url}")
    success = await client.login()

    if success:
        print("✅ [INSTAGRAM] Авторизація успішна!")
        is_valid = await client.check_session_valid()
        print(f"📊 [INSTAGRAM] Статус сесії: {'Валідна' if is_valid else 'Невалідна'}")

        # Зупиняємо монітор, щоб процес завершився
        await client.stop_proxy_monitor()
    else:
        print("❌ [INSTAGRAM] Помилка авторизації. Відкрий logs/app.log для деталей.")


if __name__ == "__main__":
    asyncio.run(test_auth())
