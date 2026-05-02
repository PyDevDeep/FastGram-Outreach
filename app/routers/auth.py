from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from pydantic import BaseModel

from app.dependencies import get_instagram_client, verify_api_key
from app.services.instagram_client import InstagramClient
from app.utils.logger import setup_logger

logger = setup_logger("auth_router")

router = APIRouter(
    prefix="/api/auth", tags=["Authentication"], dependencies=[Depends(verify_api_key)]
)


class AuthStatusResponse(BaseModel):
    is_valid: bool
    proxy_alive: bool
    message: str


class LoginRequest(BaseModel):
    verification_code: str | None = None


class LoginResponse(BaseModel):
    status: str
    message: str


@router.post("/login", response_model=LoginResponse)
async def trigger_login(
    req: LoginRequest, client: InstagramClient = Depends(get_instagram_client)
) -> LoginResponse:
    # ==========================================
    # MOCK MODE: АКТИВНО (24h COOLDOWN)
    # ==========================================
    logger.info("MOCK MODE: /login triggered. Returning fake success.")
    return LoginResponse(status="success", message="MOCK: Успішна авторизація.")

    # ==========================================
    # ORIGINAL CODE (ЗАКОМЕНТОВАНО)
    # ==========================================
    # status = await client.login(verification_code=req.verification_code)
    #
    # if status == "success":
    #     return LoginResponse(status="success", message="Успішна авторизація.")
    # elif status == "challenge_required":
    #     return LoginResponse(
    #         status="challenge_required", message="Потрібен код 2FA (перевірте SMS/App)."
    #     )
    # else:
    #     raise HTTPException(status_code=401, detail="Помилка авторизації. Перевірте логи.")


@router.get("/status", response_model=AuthStatusResponse)
async def check_auth_status(
    client: InstagramClient = Depends(get_instagram_client),
) -> AuthStatusResponse:
    # ==========================================
    # MOCK MODE: АКТИВНО (24h COOLDOWN)
    # ==========================================
    logger.info("MOCK MODE: /status triggered. Returning fake valid session.")
    return AuthStatusResponse(
        is_valid=True, proxy_alive=True, message="MOCK: Session is valid and ready."
    )

    # ==========================================
    # ORIGINAL CODE (ЗАКОМЕНТОВАНО)
    # ==========================================
    # proxy_alive = client.is_proxy_alive
    # if not proxy_alive:
    #     return AuthStatusResponse(
    #         is_valid=False, proxy_alive=False, message="Proxy is down or misconfigured."
    #     )
    #
    # if client._login_task is not None and not client._login_task.done():  # type: ignore[reportPrivateUsage]
    #     return AuthStatusResponse(
    #         is_valid=False,
    #         proxy_alive=True,
    #         message="Login in progress (waiting for 2FA code).",
    #     )
    #
    # if client.session_path.exists():
    #     try:
    #         await client._load_session_encrypted()  # type: ignore[reportPrivateUsage]
    #     except Exception as e:
    #         logger.error(f"Failed to load session for status check: {e}")
    #
    # is_valid = await client.check_session_valid()
    # msg = (
    #     "Session is valid and ready."
    #     if is_valid
    #     else "Session is missing or invalid. Needs re-login."
    # )
    # return AuthStatusResponse(is_valid=is_valid, proxy_alive=True, message=msg)
