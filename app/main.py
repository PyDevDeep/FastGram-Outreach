from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import health, outreach
from app.utils.logger import setup_logger

logger = setup_logger("fastgram_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastGram API started")
    yield
    logger.info("FastGram API stopped")


def create_app() -> FastAPI:
    app = FastAPI(title="FastGram Outreach MVP", lifespan=lifespan)

    app.include_router(health.router)
    app.include_router(outreach.router)  # Підключено новий роутер

    return app


app = create_app()
