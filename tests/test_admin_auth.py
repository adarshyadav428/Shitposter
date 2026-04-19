from fastapi.testclient import TestClient

from newsbot.api import app
from newsbot.config import settings


def test_admin_endpoints_require_token_when_configured() -> None:
    original = settings.admin_api_token
    settings.admin_api_token = "secret-token"
    try:
        client = TestClient(app)

        denied = client.get("/admin/budget")
        assert denied.status_code == 401

        allowed_header = client.get("/admin/budget", headers={"X-Admin-Token": "secret-token"})
        assert allowed_header.status_code == 200

        allowed_bearer = client.get(
            "/admin/budget",
            headers={"Authorization": "Bearer secret-token"},
        )
        assert allowed_bearer.status_code == 200
    finally:
        settings.admin_api_token = original
