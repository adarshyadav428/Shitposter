from newsbot.config import Settings
from newsbot.preflight import evaluate_preflight


def test_preflight_prod_flags_mock_ingestors_and_missing_admin_token() -> None:
    cfg = Settings(
        APP_ENV="prod",
        USE_MOCK_INGESTORS=True,
        ENABLE_REAL_RSS=False,
        ADMIN_API_TOKEN="",
        ENABLE_STATE_SNAPSHOT=True,
        STATE_BACKEND="json",
    )
    report = evaluate_preflight(cfg)
    assert report["ok"] is False
    assert "mock ingestors enabled in production" in report["issues"]
    assert "real rss ingest disabled in production" in report["issues"]
    assert "admin api token missing in production" in report["issues"]
    assert "sqlite state backend recommended for production" in report["warnings"]


def test_preflight_dev_allows_mock_with_warning() -> None:
    cfg = Settings(APP_ENV="dev", USE_MOCK_INGESTORS=True, ADMIN_API_TOKEN="")
    report = evaluate_preflight(cfg)
    assert "mock ingestors are enabled" in report["warnings"]
    assert report["production_mode"] is False


def test_preflight_x_credentials_required_when_enabled() -> None:
    cfg = Settings(APP_ENV="prod", X_ENABLED=True, X_API_KEY="", X_API_SECRET="")
    report = evaluate_preflight(cfg)
    assert "x enabled but credentials are incomplete" in report["issues"]
