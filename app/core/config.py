from pathlib import Path
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Borna Process Control API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    environment: str = "dev"
    debug: bool = True
    database_url: str = "sqlite:///./borna_chart.db"
    config_dir: Path = Path("config")
    docs_enabled: bool = True
    auth_token_ttl_hours: int = 12
    max_failed_login_attempts: int = 5
    account_lock_minutes: int = 15
    login_rate_limit_attempts: int = 10
    login_rate_limit_window_seconds: int = 60
    security_recent_event_limit: int = 20
    security_hsts_enabled: bool = False
    security_hsts_max_age_seconds: int = 31536000
    password_min_length: int = 10
    password_require_upper: bool = True
    password_require_lower: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @computed_field  # type: ignore[misc]
    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
