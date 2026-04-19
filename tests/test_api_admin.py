from fastapi.testclient import TestClient

from newsbot.api import app


def test_admin_ingestors_endpoint() -> None:
    client = TestClient(app)
    run = client.post("/run-once")
    assert run.status_code == 200

    response = client.get("/admin/ingestors")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_admin_publication_failures_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/admin/publication-failures")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_heartbeat_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/admin/heartbeat")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
