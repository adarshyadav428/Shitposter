from datetime import datetime, timezone

from pydantic import Field
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

    telegram_enabled: bool = Field(default=False, alias="TELEGRAM_ENABLED")
    bluesky_enabled: bool = Field(default=False, alias="BLUESKY_ENABLED")
    mastodon_enabled: bool = Field(default=False, alias="MASTODON_ENABLED")

    use_mock_ingestors: bool = Field(default=True, alias="USE_MOCK_INGESTORS")
    enable_real_rss: bool = Field(default=False, alias="ENABLE_REAL_RSS")
    poll_interval_seconds: int = Field(default=30, alias="POLL_INTERVAL_SECONDS")
    autopilot_enabled: bool = Field(default=True, alias="AUTOPILOT_ENABLED")
    enable_state_snapshot: bool = Field(default=True, alias="ENABLE_STATE_SNAPSHOT")
    state_snapshot_path: str = Field(
        default=".state/newsbot_state.json", alias="STATE_SNAPSHOT_PATH"
    )

    global_pause: bool = Field(default=False, alias="GLOBAL_PAUSE")


settings = Settings()
