import re
from typing import Any

import aiofiles
import aiofiles.os
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import get_instagram_client, get_outreach_engine_instance, verify_api_key
from app.services.instagram_client import InstagramClient

router = APIRouter(prefix="/api", tags=["System"], dependencies=[Depends(verify_api_key)])


class SystemStatus(BaseModel):
    engine_active: bool
    proxy_valid: bool
    account_valid: bool
    account_banned: bool


@router.get("/status", response_model=SystemStatus)
async def get_status(client: InstagramClient = Depends(get_instagram_client)) -> SystemStatus:
    try:
        engine = get_outreach_engine_instance()
        engine_active = engine.state == "running"
        is_banned = engine.state == "blocked"
    except RuntimeError:
        engine_active = False
        is_banned = False

    account_valid = await client.check_session_valid()
    proxy_valid = client.is_proxy_alive

    return SystemStatus(
        engine_active=engine_active,
        proxy_valid=proxy_valid,
        account_valid=account_valid,
        account_banned=is_banned,
    )


@router.get("/logs")
async def get_logs(limit: int = 50) -> list[dict[str, Any]]:
    log_file = "logs/app.log"
    exists = await aiofiles.os.path.exists(log_file)
    if not exists:
        return []

    async with aiofiles.open(log_file, encoding="utf-8") as f:
        lines = await f.readlines()
        lines = lines[-limit:]

    logs: list[dict[str, Any]] = []
    # Парсинг стандартного формату "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    pattern = re.compile(r"^([\d\-]+\s[\d:,]+)\s-\s(\w+)\s-\s(\w+)\s-\s(.*)$")

    for i, line in enumerate(reversed(lines)):
        match = pattern.match(line.strip())
        if match:
            timestamp, name, level, message = match.groups()
            logs.append(
                {
                    "id": i,
                    "timestamp": timestamp.replace(",", "."),
                    "event": f"[{level}] {name}",
                    "details": message,
                }
            )
        else:
            logs.append({"id": i, "timestamp": "", "event": "SYS", "details": line.strip()})

    return logs
