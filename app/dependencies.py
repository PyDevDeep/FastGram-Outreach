from functools import lru_cache

from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from app.config import get_settings
from app.services.instagram_client import InstagramClient
from app.services.notification_service import NotificationService
from app.services.outreach_engine import OutreachEngine
from app.services.pause_manager import PauseManager
from app.services.proxy_rotator import ProxyRotator
from app.services.reply_tracker import ReplyTracker
from app.services.sheets_client import GoogleSheetsClient
from app.services.warmup_manager import WarmupManager

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
settings = get_settings()


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Перевірка X-API-Key з заголовків."""
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key"
        )
    return api_key


@lru_cache
def get_instagram_client() -> InstagramClient:
    return InstagramClient()


@lru_cache
def get_sheets_client() -> GoogleSheetsClient:
    return GoogleSheetsClient()


@lru_cache
def get_warmup_manager() -> WarmupManager:
    return WarmupManager()


@lru_cache
def get_proxy_rotator() -> ProxyRotator:
    return ProxyRotator()


@lru_cache
def get_pause_manager() -> PauseManager:
    return PauseManager()


@lru_cache
def get_notification_service() -> NotificationService:
    return NotificationService()


@lru_cache
def get_outreach_engine(
    instagram_client: InstagramClient = Depends(get_instagram_client),
    sheets_client: GoogleSheetsClient = Depends(get_sheets_client),
    warmup_manager: WarmupManager = Depends(get_warmup_manager),
    proxy_rotator: ProxyRotator = Depends(get_proxy_rotator),
    pause_manager: PauseManager = Depends(get_pause_manager),
    notification_service: NotificationService = Depends(get_notification_service),
) -> OutreachEngine:
    return OutreachEngine(
        instagram_client,
        sheets_client,
        warmup_manager=warmup_manager,
        proxy_rotator=proxy_rotator,
        pause_manager=pause_manager,
        notification_service=notification_service,
    )


@lru_cache
def get_reply_tracker(
    instagram_client: InstagramClient = Depends(get_instagram_client),
    sheets_client: GoogleSheetsClient = Depends(get_sheets_client),
) -> ReplyTracker:
    return ReplyTracker(instagram_client, sheets_client)
