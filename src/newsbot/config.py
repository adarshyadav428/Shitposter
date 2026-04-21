from datetime import datetime, timezone
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    database_url: str = Field(default="sqlite:///./newsbot.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")

    x_enabled: bool = Field(default=False, alias="X_ENABLED")
    x_monthly_budget: int = Field(default=40, alias="X_MONTHLY_BUDGET")
    x_correction_budget: int = Field(default=10, alias="X_CORRECTION_BUDGET")
    x_min_gap_minutes: int = Field(default=45, alias="X_MIN_GAP_MINUTES")
    x_account_created_at: datetime = Field(
        default_factory=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc),
        alias="X_ACCOUNT_CREATED_AT",
    )
    x_api_key: str | None = Field(default=None, alias="X_API_KEY")
    x_api_secret: str | None = Field(default=None, alias="X_API_SECRET")
    x_access_token: str | None = Field(default=None, alias="X_ACCESS_TOKEN")
    x_access_token_secret: str | None = Field(default=None, alias="X_ACCESS_TOKEN_SECRET")

    telegram_enabled: bool = Field(default=False, alias="TELEGRAM_ENABLED")
    bluesky_enabled: bool = Field(default=False, alias="BLUESKY_ENABLED")
    mastodon_enabled: bool = Field(default=False, alias="MASTODON_ENABLED")
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")
    bluesky_identifier: str | None = Field(default=None, alias="BLUESKY_IDENTIFIER")
    bluesky_app_password: str | None = Field(default=None, alias="BLUESKY_APP_PASSWORD")
    mastodon_base_url: str | None = Field(default=None, alias="MASTODON_BASE_URL")
    mastodon_access_token: str | None = Field(default=None, alias="MASTODON_ACCESS_TOKEN")

    use_mock_ingestors: bool = Field(default=True, alias="USE_MOCK_INGESTORS")
    enable_real_rss: bool = Field(default=False, alias="ENABLE_REAL_RSS")
    poll_interval_seconds: int = Field(default=30, alias="POLL_INTERVAL_SECONDS")
    autopilot_enabled: bool = Field(default=True, alias="AUTOPILOT_ENABLED")
    enable_state_snapshot: bool = Field(default=True, alias="ENABLE_STATE_SNAPSHOT")
    state_backend: Literal["json", "sqlite"] = Field(default="json", alias="STATE_BACKEND")
    state_snapshot_path: str = Field(
        default=".state/newsbot_state.json", alias="STATE_SNAPSHOT_PATH"
    )
    state_sqlite_path: str = Field(
        default=".state/newsbot_state.sqlite", alias="STATE_SQLITE_PATH"
    )
    retraction_monitor_enabled: bool = Field(default=True, alias="RETRACTION_MONITOR_ENABLED")
    retraction_monitor_interval_seconds: int = Field(
        default=300, alias="RETRACTION_MONITOR_INTERVAL_SECONDS"
    )
    heartbeat_enabled: bool = Field(default=False, alias="HEARTBEAT_ENABLED")
    heartbeat_interval_seconds: int = Field(default=300, alias="HEARTBEAT_INTERVAL_SECONDS")
    enforce_startup_preflight: bool = Field(default=True, alias="ENFORCE_STARTUP_PREFLIGHT")
    admin_api_token: str | None = Field(default=None, alias="ADMIN_API_TOKEN")
    retention_enabled: bool = Field(default=True, alias="RETENTION_ENABLED")
    retention_max_events: int = Field(default=5000, alias="RETENTION_MAX_EVENTS")
    retention_max_publications: int = Field(
        default=10000, alias="RETENTION_MAX_PUBLICATIONS"
    )
    retention_max_failed_publications: int = Field(
        default=5000, alias="RETENTION_MAX_FAILED_PUBLICATIONS"
    )
    retention_max_drop_samples: int = Field(default=10000, alias="RETENTION_MAX_DROP_SAMPLES")

    global_pause: bool = Field(default=False, alias="GLOBAL_PAUSE")

    @field_validator("state_backend", mode="before")
    @classmethod
    def normalize_state_backend(cls, value: str) -> str:
        return value.lower() if isinstance(value, str) else value


settings = Settings()
