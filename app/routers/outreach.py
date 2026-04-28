import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import (
    get_outreach_engine,
    get_pause_manager,
    get_warmup_manager,
    verify_api_key,
)
from app.services.outreach_engine import OutreachEngine
from app.services.pause_manager import PauseManager
from app.services.warmup_manager import WarmupManager

router = APIRouter(prefix="/outreach", tags=["Outreach"], dependencies=[Depends(verify_api_key)])


class StartOutreachRequest(BaseModel):
    batch_size: int | None = None
    dry_run: bool = False


@router.post("/start")
async def start_outreach(
    request: StartOutreachRequest,
    background_tasks: BackgroundTasks,
    engine: OutreachEngine = Depends(get_outreach_engine),
) -> dict[str, Any]:
    if engine.state in ["running", "paused"]:
        raise HTTPException(status_code=400, detail=f"Engine is currently {engine.state}")

    task_id = str(uuid.uuid4())
    limit = request.batch_size or engine.settings.daily_message_limit
    avg_delay = (engine.settings.min_delay_seconds + engine.settings.max_delay_seconds) / 2
    est_seconds = limit * (avg_delay + 5)  # +5s на типізацію
    est_completion = (datetime.now(UTC) + timedelta(seconds=est_seconds)).isoformat()

    background_tasks.add_task(
        engine.run_batch, batch_size=request.batch_size, dry_run=request.dry_run
    )

    return {
        "task_id": task_id,
        "status": "started",
        "estimated_completion_time": est_completion,
        "batch_size": limit,
        "dry_run": request.dry_run,
    }


@router.post("/pause")
async def pause_outreach(engine: OutreachEngine = Depends(get_outreach_engine)) -> dict[str, str]:
    if engine.state != "running":
        raise HTTPException(status_code=400, detail=f"Cannot pause from state: {engine.state}")
    engine.state = "paused"
    return {"status": "paused"}


@router.post("/resume")
async def resume_outreach(engine: OutreachEngine = Depends(get_outreach_engine)) -> dict[str, str]:
    if engine.state != "paused":
        raise HTTPException(status_code=400, detail=f"Cannot resume from state: {engine.state}")
    engine.state = "running"
    return {"status": "resumed"}


@router.get("/status")
async def get_outreach_status(
    engine: OutreachEngine = Depends(get_outreach_engine),
) -> dict[str, Any]:
    pending = await engine.sheets_client.get_pending_contacts()
    return {
        "state": engine.state,
        "sent_today": engine.sent_today,
        "pending_in_sheets": len(pending),
        "failed_today": getattr(engine, "failed_today", 0),
        "last_message_time": getattr(engine, "last_message_time", None),
    }


# ------------------------------------------------------------------ #
#  Warm-up Management                                                #
# ------------------------------------------------------------------ #


@router.post("/warmup/increment")
async def increment_warmup(manager: WarmupManager = Depends(get_warmup_manager)) -> dict[str, Any]:
    """Перехід на наступний день прогріву (викликається через n8n щодня о 00:01)."""
    if not manager.is_warmup_active():
        return {
            "status": "completed",
            "message": "Warm-up already finished.",
            "current_limit": manager.get_current_daily_limit(),
        }

    new_limit = manager.increment_warmup_day()
    current_day = manager.get_current_day()

    return {
        "status": "incremented",
        "day": current_day,
        "new_limit": new_limit,
        "is_active": manager.is_warmup_active(),
    }


@router.post("/warmup/reset")
async def reset_warmup(manager: WarmupManager = Depends(get_warmup_manager)) -> dict[str, str]:
    """Примусове скидання прогріву до 1-го дня (використовувати при бані або зміні акаунта)."""
    manager.reset_warmup()
    return {"status": "reset", "message": "Warm-up reset to Day 1 (Limit: 5)"}


@router.get("/warmup/status")
async def get_warmup_status(manager: WarmupManager = Depends(get_warmup_manager)) -> dict[str, Any]:
    """Отримання поточного статусу прогріву."""
    return {
        "day": manager.get_current_day(),
        "daily_limit": manager.get_current_daily_limit(),
        "is_active": manager.is_warmup_active(),
    }


@router.post("/resume-pause")
async def manual_resume_pause(manager: PauseManager = Depends(get_pause_manager)) -> dict[str, str]:
    """Примусове зняття 24-годинної паузи (використовувати після ручного розблокування акаунта)."""
    if not manager.is_paused():
        return {"status": "ignored", "message": "System is not currently paused."}

    manager.manual_resume()
    # Якщо engine був у стані 'blocked', переводимо його в 'idle' для можливості нових запусків
    engine = get_outreach_engine()
    if engine.state == "blocked":
        engine.state = "idle"

    return {"status": "resumed", "message": "Pause lifted manually. System ready."}
