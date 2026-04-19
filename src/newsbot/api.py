from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from newsbot.config import settings
from newsbot.dashboard import render_dashboard_html
from newsbot.feed import render_events_json, render_rss_xml
from newsbot.heartbeat import HeartbeatRunner
from newsbot.main import build_default_orchestrator
from newsbot.retraction_monitor import RetractionMonitor
from newsbot.runtime import AutopilotRunner
from newsbot.state.persistence import default_state_path, save_state
from newsbot.telemetry import render_metrics

orchestrator = build_default_orchestrator()
runner = AutopilotRunner(
    orchestrator=orchestrator,
    poll_interval_seconds=settings.poll_interval_seconds,
    snapshot_path=default_state_path() if settings.enable_state_snapshot else None,
)
retraction_monitor = RetractionMonitor(
    orchestrator=orchestrator,
    interval_seconds=settings.retraction_monitor_interval_seconds,
)
heartbeat_runner = HeartbeatRunner(interval_seconds=settings.heartbeat_interval_seconds)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    if settings.autopilot_enabled:
        await runner.start()
    if settings.retraction_monitor_enabled:
        await retraction_monitor.start()
    if settings.heartbeat_enabled:
        await heartbeat_runner.start()
    try:
        yield
    finally:
        await heartbeat_runner.stop()
        await retraction_monitor.stop()
        await runner.stop()


app = FastAPI(title="Autonomous News Broadcaster", version="0.1.0", lifespan=_lifespan)


def _channel_statuses() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    rows.append(
        {
            "name": "site",
            "enabled": True,
            "mode": "internal",
            "operational": True,
        }
    )

    telegram_configured = bool(settings.telegram_bot_token and settings.telegram_chat_id)
    rows.append(
        {
            "name": "telegram",
            "enabled": settings.telegram_enabled,
            "mode": "live" if settings.telegram_enabled and telegram_configured else "noop",
            "operational": bool((not settings.telegram_enabled) or telegram_configured),
        }
    )

    bluesky_configured = bool(settings.bluesky_identifier and settings.bluesky_app_password)
    rows.append(
        {
            "name": "bluesky",
            "enabled": settings.bluesky_enabled,
            "mode": "live" if settings.bluesky_enabled and bluesky_configured else "noop",
            "operational": bool((not settings.bluesky_enabled) or bluesky_configured),
        }
    )

    mastodon_configured = bool(settings.mastodon_base_url and settings.mastodon_access_token)
    rows.append(
        {
            "name": "mastodon",
            "enabled": settings.mastodon_enabled,
            "mode": "live" if settings.mastodon_enabled and mastodon_configured else "noop",
            "operational": bool((not settings.mastodon_enabled) or mastodon_configured),
        }
    )

    x_configured = bool(
        settings.x_api_key
        and settings.x_api_secret
        and settings.x_access_token
        and settings.x_access_token_secret
    )
    rows.append(
        {
            "name": "x",
            "enabled": settings.x_enabled,
            "mode": "live" if settings.x_enabled and x_configured else "noop",
            "operational": bool((not settings.x_enabled) or x_configured),
        }
    )
    return rows


def _persistence_status() -> dict[str, Any]:
    path = default_state_path()
    parent = Path(path).parent
    return {
        "backend": settings.state_backend,
        "path": path,
        "snapshot_enabled": settings.enable_state_snapshot,
        "directory_exists": parent.exists(),
    }


def _ingest_status() -> dict[str, Any]:
    return {
        "enable_real_rss": settings.enable_real_rss,
        "use_mock_ingestors": settings.use_mock_ingestors,
        "ingestor_count": len(orchestrator.ingestors),
        "last_poll": orchestrator.get_ingestor_stats(),
    }


def _readiness_summary(issues: list[str]) -> str:
    if not issues:
        return "all core systems are operational"
    if len(issues) == 1:
        return issues[0]
    return f"{len(issues)} issues detected"


def _build_system_readiness() -> dict:
    channels = _channel_statuses()
    persistence = _persistence_status()
    ingest = _ingest_status()
    runner_status = runner.status()
    retraction_status = retraction_monitor.status()
    heartbeat_status_data = heartbeat_runner.status()

    issues: list[str] = []
    if not settings.autopilot_enabled:
        issues.append("autopilot disabled in config")
    if not runner_status.get("running") and settings.autopilot_enabled:
        issues.append("autopilot process not running")
    if ingest["ingestor_count"] == 0:
        issues.append("no ingestors configured")
    if settings.enable_state_snapshot and not persistence["directory_exists"]:
        issues.append("state directory does not exist yet")
    if not all(item["operational"] for item in channels):
        issues.append("one or more enabled channels missing credentials")
    if settings.retraction_monitor_enabled and not retraction_status.get("running"):
        issues.append("retraction monitor process not running")
    if settings.heartbeat_enabled and not heartbeat_status_data.get("running"):
        issues.append("heartbeat process not running")

    return {
        "ready": len(issues) == 0,
        "summary": _readiness_summary(issues),
        "issues": issues,
        "channels": channels,
        "persistence": persistence,
        "ingest": ingest,
        "runners": {
            "autopilot": runner_status,
            "retraction_monitor": retraction_status,
            "heartbeat": heartbeat_status_data,
        },
    }


@app.get("/")
async def index() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=307)


@app.get("/dashboard")
async def dashboard() -> HTMLResponse:
    return HTMLResponse(content=render_dashboard_html())


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready")
async def health_ready(response: Response) -> dict:
    payload = _build_system_readiness()
    response.status_code = 200 if payload["ready"] else 503
    return payload


@app.get("/system/readiness")
async def system_readiness() -> dict:
    return _build_system_readiness()


def require_admin_auth(
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None),
) -> None:
    expected = settings.admin_api_token
    if not expected:
        return

    bearer = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization.split(" ", 1)[1].strip()

    provided = x_admin_token or bearer
    if provided != expected:
        raise HTTPException(status_code=401, detail="admin_auth_required")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)


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
        "published_events": len(store.published_event_ids),
        "failed_publications": len(store.failed_publications),
        "drop_reasons": store.get_drop_reason_counts(),
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
async def events(limit: int = 100, sector: str | None = None) -> list[dict]:
    out = []
    rows = orchestrator.store.list_events()
    if sector:
        rows = [event for event in rows if event.sector.value == sector]
    for event in rows[:limit]:
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


@app.get("/events/{event_id}")
async def event_detail(event_id: str) -> dict:
    event = orchestrator.store.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")

    related_publications = [
        row for row in orchestrator.store.list_publications(limit=500) if row.event_id == event_id
    ]
    return {
        "event_id": event.event_id,
        "sector": event.sector.value,
        "headline": event.headline,
        "body": event.body,
        "first_seen_at": event.first_seen_at.isoformat(),
        "updated_at": event.updated_at.isoformat(),
        "entities": sorted(event.entities),
        "witnesses": [
            {
                "source_id": witness.source_id,
                "source_family": witness.source_family,
                "source_tier": int(witness.source_tier),
                "reputation": witness.reputation,
                "seen_at": witness.seen_at.isoformat(),
                "url": witness.url,
            }
            for witness in event.witnesses
        ],
        "published": orchestrator.store.is_published(event_id),
        "retracted": orchestrator.store.is_retracted(event_id),
        "publications": [
            {
                "channel": row.channel,
                "created_at": row.created_at.isoformat(),
                "payload": row.payload,
            }
            for row in related_publications
        ],
    }


@app.get("/events.json")
async def events_json(limit: int = 100) -> list[dict]:
    return render_events_json(orchestrator.store, limit=limit)


@app.get("/rss.xml")
async def rss_xml() -> Response:
    xml = render_rss_xml(orchestrator.store, site_url="http://localhost:8000")
    return Response(content=xml, media_type="application/rss+xml")


@app.get("/admin/publications")
async def publications(limit: int = 50, _auth: None = Depends(require_admin_auth)) -> list[dict]:
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


@app.get("/admin/publication-failures")
async def publication_failures(
    limit: int = 50, _auth: None = Depends(require_admin_auth)
) -> list[dict]:
    rows = orchestrator.store.list_failed_publications(limit=limit)
    return [
        {
            "event_id": row.event_id,
            "channel": row.channel,
            "created_at": row.created_at.isoformat(),
            "payload": row.payload,
            "error": row.error,
        }
        for row in rows
    ]


@app.get("/admin/sources")
async def sources(_auth: None = Depends(require_admin_auth)) -> dict[str, float]:
    model = orchestrator.store.source_reputation
    return {k: float(v) for k, v in model.items()}


@app.get("/admin/drops")
async def drops(limit: int = 100, _auth: None = Depends(require_admin_auth)) -> dict:
    return {
        "counts": orchestrator.store.get_drop_reason_counts(),
        "samples": orchestrator.store.list_drop_samples(limit=limit),
    }


@app.get("/admin/ingestors")
async def ingestors(_auth: None = Depends(require_admin_auth)) -> dict[str, dict[str, Any]]:
    return orchestrator.get_ingestor_stats()


@app.get("/admin/circuit")
async def circuit(_auth: None = Depends(require_admin_auth)) -> dict:
    return orchestrator.circuit_breaker.status()


@app.get("/admin/budget")
async def budget(_auth: None = Depends(require_admin_auth)) -> dict:
    store = orchestrator.store
    return {
        "x_used": store.x_used,
        "x_limit": store.x_monthly_budget,
        "x_correction_used": store.x_correction_used,
        "x_correction_limit": store.x_correction_budget,
    }


@app.get("/admin/retention")
async def retention(_auth: None = Depends(require_admin_auth)) -> dict:
    return {
        "enabled": settings.retention_enabled,
        "state_backend": settings.state_backend,
        "state_snapshot_path": settings.state_snapshot_path,
        "state_sqlite_path": settings.state_sqlite_path,
        "max_events": settings.retention_max_events,
        "max_publications": settings.retention_max_publications,
        "max_failed_publications": settings.retention_max_failed_publications,
        "max_drop_samples": settings.retention_max_drop_samples,
        "current": {
            "events": len(orchestrator.store.events),
            "publications": len(orchestrator.store.publications),
            "failed_publications": len(orchestrator.store.failed_publications),
            "drop_samples": len(orchestrator.store.drop_samples),
        },
    }


@app.post("/admin/prune")
async def prune(_auth: None = Depends(require_admin_auth)) -> dict[str, int]:
    return orchestrator.store.prune(
        max_events=settings.retention_max_events,
        max_publications=settings.retention_max_publications,
        max_failed_publications=settings.retention_max_failed_publications,
        max_drop_samples=settings.retention_max_drop_samples,
    )


@app.post("/admin/state/save")
async def save_state_snapshot(_auth: None = Depends(require_admin_auth)) -> dict:
    path = default_state_path()
    save_state(orchestrator.store, path_override=path)
    return {
        "saved": True,
        "backend": settings.state_backend,
        "path": path,
        "counts": {
            "events": len(orchestrator.store.events),
            "publications": len(orchestrator.store.publications),
            "failed_publications": len(orchestrator.store.failed_publications),
            "drop_samples": len(orchestrator.store.drop_samples),
        },
    }


@app.post("/admin/pause")
async def pause(_auth: None = Depends(require_admin_auth)) -> dict[str, bool]:
    orchestrator.store.global_pause = True
    return {"paused": True}


@app.post("/admin/resume")
async def resume(_auth: None = Depends(require_admin_auth)) -> dict[str, bool]:
    orchestrator.store.global_pause = False
    return {"paused": False}


@app.post("/admin/retract/{event_id}")
async def retract(
    event_id: str,
    reason: str = "source corrected report",
    _auth: None = Depends(require_admin_auth),
) -> dict[str, bool]:
    triggered = await orchestrator.retract(event_id, reason)
    if orchestrator.store.get_event(event_id) is None:
        raise HTTPException(status_code=404, detail="event_not_found")
    return {"correction_published": True, "circuit_breaker_triggered": triggered}


@app.get("/admin/autopilot")
async def autopilot_status(_auth: None = Depends(require_admin_auth)) -> dict:
    return runner.status()


@app.post("/admin/autopilot/start")
async def autopilot_start(_auth: None = Depends(require_admin_auth)) -> dict:
    started = await runner.start()
    return {"started": started, "status": runner.status()}


@app.post("/admin/autopilot/stop")
async def autopilot_stop(_auth: None = Depends(require_admin_auth)) -> dict:
    stopped = await runner.stop()
    return {"stopped": stopped, "status": runner.status()}


@app.get("/admin/retraction-monitor")
async def retraction_monitor_status(_auth: None = Depends(require_admin_auth)) -> dict:
    return retraction_monitor.status()


@app.post("/admin/retraction-monitor/start")
async def retraction_monitor_start(_auth: None = Depends(require_admin_auth)) -> dict:
    started = await retraction_monitor.start()
    return {"started": started, "status": retraction_monitor.status()}


@app.post("/admin/retraction-monitor/stop")
async def retraction_monitor_stop(_auth: None = Depends(require_admin_auth)) -> dict:
    stopped = await retraction_monitor.stop()
    return {"stopped": stopped, "status": retraction_monitor.status()}


@app.post("/admin/retraction-monitor/scan")
async def retraction_monitor_scan(_auth: None = Depends(require_admin_auth)) -> dict[str, int]:
    triggered = await retraction_monitor.scan_once()
    return {"triggered": triggered}


@app.get("/admin/heartbeat")
async def heartbeat_status(_auth: None = Depends(require_admin_auth)) -> dict:
    return heartbeat_runner.status()


@app.post("/admin/heartbeat/start")
async def heartbeat_start(_auth: None = Depends(require_admin_auth)) -> dict:
    started = await heartbeat_runner.start()
    return {"started": started, "status": heartbeat_runner.status()}


@app.post("/admin/heartbeat/stop")
async def heartbeat_stop(_auth: None = Depends(require_admin_auth)) -> dict:
    stopped = await heartbeat_runner.stop()
    return {"stopped": stopped, "status": heartbeat_runner.status()}


@app.post("/admin/heartbeat/send")
async def heartbeat_send(_auth: None = Depends(require_admin_auth)) -> dict[str, bool]:
    sent = await heartbeat_runner.send_once()
    return {"sent": sent}
