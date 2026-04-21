import pytest
from fastapi.testclient import TestClient

from newsbot.api import app
from newsbot.config import settings


def test_root_redirects_to_dashboard() -> None:
    client = TestClient(app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/dashboard"


def test_dashboard_returns_html() -> None:
    client = TestClient(app)
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Autonomous News Ops Console" in response.text


def test_system_readiness_shape() -> None:
    client = TestClient(app)
    response = client.get("/system/readiness")
    assert response.status_code == 200
    payload = response.json()
    assert "ready" in payload
    assert "summary" in payload
    assert "issues" in payload
    assert "warnings" in payload
    assert "environment" in payload
    assert "channels" in payload
    assert "persistence" in payload
    assert "ingest" in payload
    assert "runners" in payload


def test_system_preflight_shape() -> None:
    client = TestClient(app)
    response = client.get("/system/preflight")
    assert response.status_code == 200
    payload = response.json()
    assert "environment" in payload
    assert "production_mode" in payload
    assert "issues" in payload
    assert "warnings" in payload
    assert "ok" in payload


def test_liveness_probe() -> None:
    client = TestClient(app)
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "live"


def test_readiness_probe_returns_503_when_autopilot_disabled() -> None:
    original = settings.autopilot_enabled
    settings.autopilot_enabled = False
    try:
        client = TestClient(app)
        response = client.get("/health/ready")
        assert response.status_code == 503
        payload = response.json()
        assert payload["ready"] is False
        assert "autopilot disabled in config" in payload["issues"]
    finally:
        settings.autopilot_enabled = original


def test_startup_fails_when_prod_preflight_enforced_and_invalid() -> None:
    original_app_env = settings.app_env
    original_use_mock = settings.use_mock_ingestors
    original_real_rss = settings.enable_real_rss
    original_admin_token = settings.admin_api_token
    original_enforce_preflight = settings.enforce_startup_preflight
    try:
        settings.app_env = "prod"
        settings.use_mock_ingestors = True
        settings.enable_real_rss = False
        settings.admin_api_token = ""
        settings.enforce_startup_preflight = True
        with pytest.raises(RuntimeError):
            with TestClient(app):
                pass
    finally:
        settings.app_env = original_app_env
        settings.use_mock_ingestors = original_use_mock
        settings.enable_real_rss = original_real_rss
        settings.admin_api_token = original_admin_token
        settings.enforce_startup_preflight = original_enforce_preflight


def test_startup_allows_invalid_prod_when_preflight_enforcement_disabled() -> None:
    original_app_env = settings.app_env
    original_use_mock = settings.use_mock_ingestors
    original_real_rss = settings.enable_real_rss
    original_admin_token = settings.admin_api_token
    original_enforce_preflight = settings.enforce_startup_preflight
    try:
        settings.app_env = "prod"
        settings.use_mock_ingestors = True
        settings.enable_real_rss = False
        settings.admin_api_token = ""
        settings.enforce_startup_preflight = False
        with TestClient(app) as client:
            response = client.get("/health/live")
            assert response.status_code == 200
    finally:
        settings.app_env = original_app_env
        settings.use_mock_ingestors = original_use_mock
        settings.enable_real_rss = original_real_rss
        settings.admin_api_token = original_admin_token
        settings.enforce_startup_preflight = original_enforce_preflight
