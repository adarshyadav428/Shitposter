from fastapi.testclient import TestClient

from newsbot.api import app


def test_admin_ingestors_endpoint() -> None:
    client = TestClient(app)
    run = client.post("/run-once")
    assert run.status_code == 200

    response = client.get("/admin/ingestors")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
