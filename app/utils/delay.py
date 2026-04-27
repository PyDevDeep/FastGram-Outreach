import asyncio
import secrets

from app.utils.logger import setup_logger

logger = setup_logger("delay_utils")


async def random_delay(min_seconds: float, max_seconds: float, sigma_spread: float = 6.0) -> float:
    """
    Асинхронна пауза з нормальним розподілом (Gaussian).
    Більшість значень будуть групуватися ближче до середнього.
    """
    if min_seconds >= max_seconds:
        delay = float(min_seconds)
    else:
        mean = (min_seconds + max_seconds) / 2.0
        # Розрахунок стандартного відхилення на основі заданого розмаху сигм
        std_dev = (max_seconds - min_seconds) / sigma_spread

        secure_random = secrets.SystemRandom()
        delay = secure_random.gauss(mean, std_dev)

        # Жорстко обрізаємо аномалії, що вийшли за межі
        delay = max(min_seconds, min(max_seconds, delay))

    logger.info(f"Human-like delay: sleeping for {delay:.2f} seconds")
    await asyncio.sleep(delay)
    return delay


async def typing_simulation_delay(
    message_length: int,
    chars_per_second: float = 3.15,
    noise_min: float = 0.9,
    noise_max: float = 1.1,
) -> float:
    """
    Імітація набору тексту.
    Додає випадковий шум до розрахункового часу (за замовчуванням +/- 10%).
    для відповідності критеріям (28-35 сек для 100 символів).
    """
    if message_length <= 0:
        return 0.0

    base_delay = message_length / chars_per_second
    secure_random = secrets.SystemRandom()
    noise_factor = secure_random.uniform(noise_min, noise_max)
    delay = base_delay * noise_factor

    logger.info(f"Typing simulation: sleeping for {delay:.2f} seconds ({message_length} chars)")
    await asyncio.sleep(delay)
    return delay
