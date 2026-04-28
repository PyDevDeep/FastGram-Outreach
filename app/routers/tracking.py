from typing import Any

from fastapi import APIRouter, Depends

from app.dependencies import get_reply_tracker, verify_api_key
from app.services.reply_tracker import ReplyTracker

router = APIRouter(prefix="/tracking", tags=["Tracking"], dependencies=[Depends(verify_api_key)])


@router.get("/check-replies")
async def check_replies(tracker: ReplyTracker = Depends(get_reply_tracker)) -> dict[str, Any]:
    """
    Запускає перевірку inbox, класифікує нові відповіді
    та оновлює статуси в Google Sheets.
    """
    stats = await tracker.process_and_tag()
    return stats
