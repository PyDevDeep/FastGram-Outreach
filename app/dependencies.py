from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from app.config import get_settings
from app.services.instagram_client import InstagramClient
from app.services.outreach_engine import OutreachEngine
from app.services.sheets_client import GoogleSheetsClient

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
settings = get_settings()

# Singleton-інстанси
_instagram_client = InstagramClient()
_sheets_client = GoogleSheetsClient()
_outreach_engine = OutreachEngine(_instagram_client, _sheets_client)


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
