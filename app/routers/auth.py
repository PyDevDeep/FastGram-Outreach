from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import get_instagram_client, verify_api_key
from app.services.instagram_client import InstagramClient
from app.utils.logger import setup_logger

logger = setup_logger("auth_router")

# ДОДАНО: dependencies=[Depends(verify_api_key)]
# Тепер кожен запит до цього роутера зобов'язаний мати правильний X-API-Key
router = APIRouter(prefix="/auth", tags=["Authentication"], dependencies=[Depends(verify_api_key)])


class AuthStatusResponse(BaseModel):
    is_valid: bool
    proxy_alive: bool
    message: str


@router.get("/status", response_model=AuthStatusResponse)
async def check_auth_status(client: InstagramClient = Depends(get_instagram_client)):
    """Перевіряє, чи жива поточна сесія та проксі."""
    proxy_alive = client.is_proxy_alive
    if not proxy_alive:
        return AuthStatusResponse(
            is_valid=False, proxy_alive=False, message="Proxy is down or misconfigured."
        )

    is_valid = await client.check_session_valid()
    msg = (
        "Session is valid and ready."
        if is_valid
        else "Session is missing or invalid. Needs re-login."
    )
    return AuthStatusResponse(is_valid=is_valid, proxy_alive=True, message=msg)
