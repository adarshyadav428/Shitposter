from fastapi.testclient import TestClient

from newsbot.api import app


def test_metrics_endpoint_exposes_core_counters() -> None:
    client = TestClient(app)
    run = client.post("/run-once")
    assert run.status_code == 200

    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "newsbot_runs_total" in body
    assert "newsbot_raw_events_total" in body
    assert "newsbot_published_events_total" in body
