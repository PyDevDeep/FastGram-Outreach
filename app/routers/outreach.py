from fastapi import APIRouter, Depends

from app.dependencies import get_instagram_client, verify_api_key
from app.services.instagram_client import InstagramClient

# Застосовуємо API Key залежність до всього роутера
router = APIRouter(prefix="/outreach", tags=["Outreach"], dependencies=[Depends(verify_api_key)])


@router.post("/start")
async def start_outreach(client: InstagramClient = Depends(get_instagram_client)) -> dict[str, str]:
    """
    Базова версія для ініціалізації сесії (Task 1.1.2).
    Повна логіка черги буде додана у Phase 2.
    """
    is_valid = await client.check_session_valid()

    if is_valid:
        return {"session_status": "active"}

    login_success = await client.login()

    if login_success:
        return {"session_status": "logged_in"}

    return {"session_status": "failed_to_login"}
