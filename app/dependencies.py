from functools import lru_cache

from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from instagrapi import Client  # type: ignore[reportMissingTypeStubs]
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_session
from app.repositories.lead_repository import LeadRepository
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

# Singleton OutreachEngine at the module level.
# lru_cache + Depends are incompatible: FastAPI doesn't pass Depends arguments
# to lru_cache function when called outside DI context (e.g. in lifespan).
_outreach_engine: OutreachEngine | None = None


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Check X-API-Key from headers."""
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key"
        )
    return api_key


def get_lead_repository(session: AsyncSession = Depends(get_db_session)) -> LeadRepository:
    return LeadRepository(session)


@lru_cache
def get_instagram_client() -> InstagramClient:
    return InstagramClient(settings=get_settings(), client_factory=Client)


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


def get_outreach_engine(
    instagram_client: InstagramClient = Depends(get_instagram_client),
    sheets_client: GoogleSheetsClient = Depends(get_sheets_client),
    lead_repository: LeadRepository = Depends(get_lead_repository),
    warmup_manager: WarmupManager = Depends(get_warmup_manager),
    proxy_rotator: ProxyRotator = Depends(get_proxy_rotator),
    pause_manager: PauseManager = Depends(get_pause_manager),
    notification_service: NotificationService = Depends(get_notification_service),
) -> OutreachEngine:
    """
    FastAPI dependency — returns the OutreachEngine singleton.
    First call initializes the instance and stores it in _outreach_engine.
    Subsequent calls (including from lifespan via get_outreach_engine_instance)
    return the same object.
    """
    global _outreach_engine
    if _outreach_engine is None:
        _outreach_engine = OutreachEngine(
            instagram_client,
            sheets_client,
            lead_repository=lead_repository,
            warmup_manager=warmup_manager,
            proxy_rotator=proxy_rotator,
            pause_manager=pause_manager,
            notification_service=notification_service,
        )
    return _outreach_engine


def get_outreach_engine_instance() -> OutreachEngine:
    """
    Returns the already created OutreachEngine singleton outside DI context
    (e.g., in lifespan or background tasks).
    Raises RuntimeError if called before the first HTTP request.
    """
    if _outreach_engine is None:
        raise RuntimeError(
            "OutreachEngine is not initialized yet. "
            "Ensure at least one request has been processed before calling this."
        )
    return _outreach_engine


@lru_cache
def get_reply_tracker(
    instagram_client: InstagramClient = Depends(get_instagram_client),
    sheets_client: GoogleSheetsClient = Depends(get_sheets_client),
) -> ReplyTracker:
    return ReplyTracker(instagram_client, sheets_client)
