import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.dependencies import get_outreach_engine
from app.routers import auth, health, outreach, tracking
from app.utils.logger import setup_logger

logger = setup_logger("fastgram_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Event ---
    logger.info("Starting FastGram API...")
    yield
    # --- Shutdown Event ---
    logger.info("Received shutdown signal. Initiating graceful shutdown...")
    engine = get_outreach_engine()

    if engine.state == "running":
        engine.state = "stopping"
        logger.info(
            "Engine is running. Waiting up to 15 seconds for the current request to finish..."
        )

        # Даємо до 15 секунд на завершення поточного HTTP-запиту
        for _ in range(15):
            if engine.state == "idle":  # type: ignore[reportUnnecessaryComparison]
                logger.info("Engine returned to idle gracefully.")
                break
            await asyncio.sleep(1)

    logger.info("Shutdown complete. Good bye!")


def create_app() -> FastAPI:
    app = FastAPI(
        title="FastGram Outreach API",
        description="API for automated Instagram DMs",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(health.router)
    app.include_router(outreach.router)  # Підключено новий роутер
    app.include_router(tracking.router)  # Підключено роутер відстеження
    app.include_router(auth.router)  # Підключено роутер авторизації

    return app


app = create_app()
