from fastapi.testclient import TestClient

from newsbot.api import app


def test_events_json_endpoint() -> None:
    client = TestClient(app)
    run = client.post("/run-once")
    assert run.status_code == 200

    response = client.get("/events.json")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_rss_endpoint() -> None:
    client = TestClient(app)
    client.post("/run-once")
    response = client.get("/rss.xml")
    assert response.status_code == 200
    assert "<rss version=\"2.0\">" in response.text
    assert "<channel>" in response.text
