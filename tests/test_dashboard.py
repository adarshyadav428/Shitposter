from fastapi.testclient import TestClient

from newsbot.api import app


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
    assert "channels" in payload
    assert "persistence" in payload
    assert "ingest" in payload
    assert "runners" in payload
