import json
from pathlib import Path

import aiofiles
import aiofiles.os
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import verify_api_key

router = APIRouter(prefix="/api/config", tags=["Config"], dependencies=[Depends(verify_api_key)])

CONFIG_FILE = Path("app/state/system_config.json")


class SystemConfig(BaseModel):
    max_daily: int = 20
    message_template: str = "Hi, interested?"
    initial_limit: int = 5
    step: int = 5
    min_seconds: int = 30
    max_seconds: int = 60
    work_hours_start: int = 9
    work_hours_end: int = 21


@router.get("/", response_model=SystemConfig)
async def get_config() -> SystemConfig:
    exists = await aiofiles.os.path.exists(CONFIG_FILE)
    if not exists:
        return SystemConfig()
    async with aiofiles.open(CONFIG_FILE, encoding="utf-8") as f:
        content = await f.read()
        return SystemConfig(**json.loads(content))


@router.post("/", response_model=SystemConfig)
async def save_config(config: SystemConfig) -> SystemConfig:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(CONFIG_FILE, "w", encoding="utf-8") as f:
        await f.write(json.dumps(config.model_dump(), indent=4))
    return config
