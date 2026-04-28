from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from app.config import get_settings
from app.services.instagram_client import InstagramClient
from app.services.outreach_engine import OutreachEngine
from app.services.proxy_rotator import ProxyRotator
from app.services.reply_tracker import ReplyTracker
from app.services.sheets_client import GoogleSheetsClient
from app.services.warmup_manager import WarmupManager

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
settings = get_settings()

# Singleton-інстанси
_instagram_client = InstagramClient()
_sheets_client = GoogleSheetsClient()
_warmup_manager = WarmupManager()
_proxy_rotator = ProxyRotator()
_outreach_engine = OutreachEngine(
    _instagram_client, _sheets_client, warmup_manager=_warmup_manager, proxy_rotator=_proxy_rotator
)
_reply_tracker = ReplyTracker(_instagram_client, _sheets_client)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Перевірка X-API-Key з заголовків."""
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key"
        )
    return api_key


def get_instagram_client() -> InstagramClient:
    return _instagram_client


def get_outreach_engine() -> OutreachEngine:
    return _outreach_engine


def get_reply_tracker() -> ReplyTracker:
    return _reply_tracker


def get_warmup_manager() -> WarmupManager:
    return _warmup_manager
