from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: str = "dev_key"
    instagram_username: str = ""
    instagram_password: str = ""
    proxy_url: str = ""
    session_file_path: str = "/app/sessions/session.json"
    daily_message_limit: int = 20
    min_delay_seconds: int = 60
    max_delay_seconds: int = 300
    polling_interval_minutes: int = 30
    session_encryption_key: str = ""

    # Налаштування моніторингу проксі
    proxy_check_interval: int = Field(default=60)
    proxy_check_timeout: int = Field(default=10)
    proxy_max_failures: int = Field(default=2)

    google_sheets_id: str = ""
    google_application_credentials: str = "/app/credentials.json"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
