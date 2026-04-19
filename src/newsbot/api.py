from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from newsbot.config import settings
from newsbot.main import build_default_orchestrator
from newsbot.runtime import AutopilotRunner

orchestrator = build_default_orchestrator()
runner = AutopilotRunner(
    orchestrator=orchestrator,
    poll_interval_seconds=settings.poll_interval_seconds,
    snapshot_path=settings.state_snapshot_path if settings.enable_state_snapshot else None,
)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    if settings.autopilot_enabled:
        await runner.start()
    try:
        yield
    finally:
        await runner.stop()


app = FastAPI(title="Autonomous News Broadcaster", version="0.1.0", lifespan=_lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run-once")
async def run_once() -> dict[str, int]:
    return await runner.run_once_now()


@app.get("/stats")
async def stats() -> dict:
    store = orchestrator.store
    return {
        "autopilot": runner.status(),
        "events": len(store.events),
        "publications": len(store.publications),
        "x_budget": {
            "used": store.x_used,
            "limit": store.x_monthly_budget,
            "correction_used": store.x_correction_used,
            "correction_limit": store.x_correction_budget,
        },
        "paused": {
            "global": store.global_pause,
            "sector": {k.value: v for k, v in store.sector_paused.items()},
        },
    }


@app.get("/events")
async def events() -> list[dict]:
    out = []
    for event in orchestrator.store.list_events():
        out.append(
            {
                "event_id": event.event_id,
                "sector": event.sector.value,
                "headline": event.headline,
                "updated_at": event.updated_at.isoformat(),
                "witnesses": len(event.witnesses),
            }
        )
    return out


@app.get("/admin/publications")
async def publications(limit: int = 50) -> list[dict]:
    rows = orchestrator.store.list_publications(limit=limit)
    return [
        {
            "event_id": row.event_id,
            "channel": row.channel,
            "created_at": row.created_at.isoformat(),
            "payload": row.payload,
        }
        for row in rows
    ]


@app.get("/admin/sources")
async def sources() -> dict[str, float]:
    model = orchestrator.store.source_reputation
    return {k: float(v) for k, v in model.items()}


@app.get("/admin/circuit")
async def circuit() -> dict:
    return orchestrator.circuit_breaker.status()


@app.get("/admin/budget")
async def budget() -> dict:
    store = orchestrator.store
    return {
        "x_used": store.x_used,
        "x_limit": store.x_monthly_budget,
        "x_correction_used": store.x_correction_used,
        "x_correction_limit": store.x_correction_budget,
    }


@app.post("/admin/pause")
async def pause() -> dict[str, bool]:
    orchestrator.store.global_pause = True
    return {"paused": True}


@app.post("/admin/resume")
async def resume() -> dict[str, bool]:
    orchestrator.store.global_pause = False
    return {"paused": False}


@app.post("/admin/retract/{event_id}")
async def retract(event_id: str, reason: str = "source corrected report") -> dict[str, bool]:
    triggered = await orchestrator.retract(event_id, reason)
    if orchestrator.store.get_event(event_id) is None:
        raise HTTPException(status_code=404, detail="event_not_found")
    return {"correction_published": True, "circuit_breaker_triggered": triggered}


@app.get("/admin/autopilot")
async def autopilot_status() -> dict:
    return runner.status()


@app.post("/admin/autopilot/start")
async def autopilot_start() -> dict:
    started = await runner.start()
    return {"started": started, "status": runner.status()}


@app.post("/admin/autopilot/stop")
async def autopilot_stop() -> dict:
    stopped = await runner.stop()
    return {"stopped": stopped, "status": runner.status()}
