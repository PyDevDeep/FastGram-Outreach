from typing import Any

from fastapi import APIRouter, Depends

from app.dependencies import get_instagram_client, get_sheets_client
from app.services.instagram_client import InstagramClient
from app.services.sheets_client import GoogleSheetsClient
from app.utils.logger import setup_logger

logger = setup_logger("health")

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(
    ig_client: InstagramClient = Depends(get_instagram_client),
    sheets_client: GoogleSheetsClient = Depends(get_sheets_client),
) -> dict[str, Any]:
    ig_session_active = await ig_client.check_session_valid()

    sheets_connected = False
    try:
        if sheets_client.sheet:
            sheets_connected = True
    except Exception as e:
        logger.warning(f"Sheets connection check failed: {e}")

    proxy_reachable = ig_client.is_proxy_alive if ig_client.settings.proxy_url else True

    overall_status = (
        "ok" if (ig_session_active and sheets_connected and proxy_reachable) else "degraded"
    )

    return {
        "status": overall_status,
        "instagram_session": "active" if ig_session_active else "expired",
        "google_sheets": "connected" if sheets_connected else "error",
        "proxy": "reachable" if proxy_reachable else "unreachable",
    }
