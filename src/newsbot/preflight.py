from __future__ import annotations

from typing import Any

from newsbot.config import Settings


def is_production_env(app_env: str) -> bool:
    normalized = (app_env or "").strip().lower()
    return normalized in {"prod", "production"}


def evaluate_preflight(settings: Settings) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []

    prod = is_production_env(settings.app_env)

    if prod:
        if settings.use_mock_ingestors:
            issues.append("mock ingestors enabled in production")
        if not settings.enable_real_rss:
            issues.append("real rss ingest disabled in production")
        if not settings.admin_api_token:
            issues.append("admin api token missing in production")
        if not settings.enable_state_snapshot:
            issues.append("state snapshot disabled in production")
        if settings.state_backend != "sqlite":
            warnings.append("sqlite state backend recommended for production")
    else:
        if not settings.admin_api_token:
            warnings.append("admin api token is not set")
        if settings.use_mock_ingestors:
            warnings.append("mock ingestors are enabled")

    if settings.x_enabled and not (
        settings.x_api_key
        and settings.x_api_secret
        and settings.x_access_token
        and settings.x_access_token_secret
    ):
        issues.append("x enabled but credentials are incomplete")

    return {
        "environment": settings.app_env,
        "production_mode": prod,
        "issues": issues,
        "warnings": warnings,
        "ok": len(issues) == 0,
    }
