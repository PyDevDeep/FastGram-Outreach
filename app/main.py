import asyncio
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import get_outreach_engine_instance
from app.routers import auth, health, leads, outreach, tracking
from app.utils.logger import setup_logger

logger = setup_logger("fastgram_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Event ---
    logger.info("Starting FastGram API...")
    yield
    # --- Shutdown Event ---
    logger.info("Received shutdown signal. Initiating graceful shutdown...")

    try:
        engine = get_outreach_engine_instance()
    except RuntimeError:
        logger.info("OutreachEngine was never initialized. Skipping graceful shutdown.")
        logger.info("Shutdown complete. Good bye!")
        return

    if engine.state == "running":
        engine.state = "stopping"
        logger.info(
            "Engine is running. Waiting up to 15 seconds for the current batch to finish..."
        )

        for _ in range(15):
            current_state = cast(str, engine.state)
            if current_state == "idle":
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # На етапі деплою замінити на конкретний домен
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(outreach.router)
    app.include_router(tracking.router)
    app.include_router(auth.router)
    app.include_router(leads.router)

    return app


app = create_app()
