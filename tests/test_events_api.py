from fastapi.testclient import TestClient

from newsbot.api import app


def test_event_detail_endpoint_returns_full_payload() -> None:
    client = TestClient(app)
    run = client.post("/run-once")
    assert run.status_code == 200

    events = client.get("/events")
    assert events.status_code == 200
    data = events.json()
    assert len(data) >= 1

    event_id = data[0]["event_id"]
    detail = client.get(f"/events/{event_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["event_id"] == event_id
    assert "witnesses" in body
    assert "publications" in body


def test_events_endpoint_supports_limit_and_sector_filters() -> None:
    client = TestClient(app)
    run = client.post("/run-once")
    assert run.status_code == 200

    limited = client.get("/events", params={"limit": 1})
    assert limited.status_code == 200
    assert len(limited.json()) <= 1

    macro = client.get("/events", params={"sector": "macroeconomics", "limit": 10})
    assert macro.status_code == 200
    for item in macro.json():
        assert item["sector"] == "macroeconomics"
