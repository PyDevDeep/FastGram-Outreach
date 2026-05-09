import asyncio
import secrets

from app.utils.logger import setup_logger

logger = setup_logger("delay_utils")


async def random_delay(min_seconds: float, max_seconds: float, sigma_spread: float = 6.0) -> float:
    """
    Asynchronous pause with normal distribution (Gaussian).
    Most values will be clustered around the mean.
    """
    if min_seconds >= max_seconds:
        delay = float(min_seconds)
    else:
        mean = (min_seconds + max_seconds) / 2.0
        # Calculate standard deviation based on the given sigma spread
        std_dev = (max_seconds - min_seconds) / sigma_spread

        secure_random = secrets.SystemRandom()
        delay = secure_random.gauss(mean, std_dev)

        # Hard clip anomalies that fall outside the boundaries
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
    Typing simulation.
    Adds random noise to the calculated time (default +/- 10%).
    to match the criteria (28-35 sec for 100 characters).
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
