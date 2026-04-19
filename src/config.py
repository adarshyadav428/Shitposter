from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://shitposter:shitposter@localhost:5432/shitposter"
    redis_url: str = "redis://localhost:6379/0"
    domain: str = "localhost"

    anthropic_api_key: str = ""
    model_compose: str = "claude-sonnet-4-6"
    model_fast: str = "claude-haiku-4-5-20251001"

    x_consumer_key: str = ""
    x_consumer_secret: str = ""
    x_access_token: str = ""
    x_access_secret: str = ""
    x_bearer_token: str = ""
    x_monthly_write_budget: int = 50
    x_correction_reserve: int = 10
    x_account_created_at: str = ""  # ISO date e.g. "2025-01-01" for warmup gate
    nitter_instances: str = "https://nitter.net,https://nitter.poast.org"

    telegram_api_id: int | None = None
    telegram_api_hash: str = ""
    telegram_bot_token: str = ""
    telegram_channel_id: str = ""
    telegram_heartbeat_channel_id: str = ""

    bluesky_handle: str = ""
    bluesky_app_password: str = ""

    mastodon_instance: str = "https://mastodon.social"
    mastodon_access_token: str = ""

    verify_t2_hold_seconds: int = 90
    cluster_window_seconds: int = 900
    simhash_hamming_threshold: int = 6
    publish_confidence_threshold: float = 0.6
    x_post_threshold: float = 0.85
    kill_switch_key: str = "pipeline:paused"

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    environment: Literal["dev", "shadow", "prod"] = Field(default="dev")

    @property
    def nitter_hosts(self) -> list[str]:
        return [s.strip() for s in self.nitter_instances.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
