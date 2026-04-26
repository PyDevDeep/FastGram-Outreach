from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from app.config import get_settings
from app.services.instagram_client import InstagramClient

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
settings = get_settings()

# Singleton-інстанс клієнта для всього життєвого циклу додатку
_instagram_client = InstagramClient()


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Перевірка X-API-Key з заголовків."""
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key"
        )
    return api_key


def get_instagram_client() -> InstagramClient:
    """Провайдер Instagram клієнта."""
    return _instagram_client
