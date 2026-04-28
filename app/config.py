from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: str = "dev_key"
    instagram_username: str = ""
    instagram_password: str = ""
    proxy_url: str = ""
    session_file_path: str = str(Path("sessions") / "session.json")
    daily_message_limit: int = 20
    min_delay_seconds: int = 60
    max_delay_seconds: int = 300
    min_delay_seconds: int = Field(default=30)
    max_delay_seconds: int = Field(default=60)

    # Proxy API settings
    proxy_api_url: str | None = Field(default=None)
    proxy_api_key: str | None = Field(default=None)
    proxy_check_interval: int = Field(default=60)
    proxy_check_timeout: int = Field(default=10)
    proxy_max_failures: int = Field(default=2)

    polling_interval_minutes: int = 30
    session_encryption_key: str = ""
    instagram_locale: str = "uk_UA"
    timezone_offset: int = 10800  # секунди від UTC, UTC+3 = 3*3600

    google_sheets_id: str = ""
    google_application_credentials: str = "/app/credentials.json"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
