"""FastAPI orchestrator + operator dashboard."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import func, select  # noqa: F401 – select used in admin routes

from src.config import get_settings
from src.heartbeat import run_forever as heartbeat_loop
from src.obs.logs import configure_logging, get_logger
from src.orchestrator import Orchestrator
from src.publish.site import recent_events, render_rss
from src.state.circuit_breaker import resume_sector, sector_status
from src.state.db import session_scope
from src.state.models import CanonicalEvent, Publication, Source
from src.state.redis_bus import client

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    orch = Orchestrator()
    await orch.start()
    hb_task = asyncio.create_task(heartbeat_loop(), name="heartbeat")
    app.state.orchestrator = orch
    app.state.heartbeat = hb_task
    log.info("app.started", env=settings.environment)
    try:
        yield
    finally:
        hb_task.cancel()
        await orch.stop()


app = FastAPI(title="Shitposter Wire", lifespan=lifespan)


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/stats")
async def stats() -> dict:
    async with session_scope() as s:
        totals = (
            await s.execute(
                select(CanonicalEvent.state, func.count())
                .group_by(CanonicalEvent.state)
            )
        ).all()
        per_channel = (
            await s.execute(
                select(Publication.channel, func.count()).group_by(Publication.channel)
            )
        ).all()
        retracted = (
            await s.execute(
                select(func.count())
                .select_from(CanonicalEvent)
                .where(CanonicalEvent.retracted.is_(True))
            )
        ).scalar() or 0
    return {
        "events_by_state": {k: v for k, v in totals},
        "publications_by_channel": {k: v for k, v in per_channel},
        "retracted": retracted,
    }


@app.get("/events.json")
async def events_json() -> JSONResponse:
    return JSONResponse(await recent_events(100))


@app.get("/rss")
async def rss() -> Response:
    settings = get_settings()
    body = await render_rss(f"https://{settings.domain}")
    return Response(body, media_type="application/rss+xml")


@app.post("/admin/pause")
async def pause() -> dict:
    settings = get_settings()
    await client().set(settings.kill_switch_key, "1")
    return {"paused": True}


@app.post("/admin/resume")
async def resume() -> dict:
    settings = get_settings()
    await client().delete(settings.kill_switch_key)
    return {"paused": False}


@app.post("/admin/retract/{event_id}")
async def retract(event_id: int) -> dict:
    from datetime import UTC, datetime

    async with session_scope() as s:
        ev = await s.get(CanonicalEvent, event_id)
        if ev is None:
            raise HTTPException(404, "not_found")
        ev.retracted = True
        ev.retracted_at = datetime.now(UTC)
    return {"ok": True, "event_id": event_id}


@app.get("/events/{event_id}")
async def event_detail(event_id: int) -> dict:
    async with session_scope() as s:
        ev = await s.get(CanonicalEvent, event_id)
        if ev is None:
            raise HTTPException(404, "not_found")
        pubs = (
            await s.execute(
                select(Publication).where(Publication.event_id == event_id)
            )
        ).scalars().all()
    return {
        "id": ev.id,
        "sector": ev.sector,
        "title": ev.title,
        "draft": ev.draft,
        "confidence": ev.confidence,
        "state": ev.state,
        "drop_reason": ev.drop_reason,
        "retracted": ev.retracted,
        "retracted_at": ev.retracted_at.isoformat() if ev.retracted_at else None,
        "first_seen_at": ev.first_seen_at.isoformat(),
        "last_seen_at": ev.last_seen_at.isoformat(),
        "entities": ev.entities,
        "claims": ev.claims,
        "publications": [
            {
                "channel": p.channel,
                "body": p.body,
                "external_id": p.external_id,
                "posted_at": p.posted_at.isoformat(),
                "corrected": p.corrected,
            }
            for p in pubs
        ],
    }


@app.get("/admin/budget")
async def budget_status() -> dict:
    from datetime import UTC, datetime

    from src.state.models import RateBudget
    from src.survival.cadence import can_post_x

    now = datetime.now(UTC)
    month_key = f"x_month:{now.strftime('%Y%m')}"
    async with session_scope() as s:
        b = await s.get(RateBudget, month_key)
    ok, remaining = await can_post_x()
    return {
        "month": now.strftime("%Y-%m"),
        "used": b.used if b else 0,
        "cap": b.cap if b else 0,
        "remaining": remaining,
        "budget_ok": ok,
    }


@app.get("/admin/sources")
async def list_sources() -> list[dict]:
    async with session_scope() as s:
        rows = (await s.execute(select(Source).order_by(Source.tier, Source.id))).scalars().all()
    return [
        {
            "id": r.id,
            "family": r.family,
            "tier": r.tier,
            "sector": r.sector,
            "reputation": round(r.reputation, 4),
            "rep_alpha": r.rep_alpha,
            "rep_beta": r.rep_beta,
            "active": r.active,
            "cooldown_until": r.cooldown_until.isoformat() if r.cooldown_until else None,
        }
        for r in rows
    ]


@app.get("/admin/circuit")
async def circuit_status() -> dict:
    return await sector_status()


@app.post("/admin/circuit/{sector}/resume")
async def circuit_resume(sector: str) -> dict:
    if sector not in ("macro", "crypto", "geo"):
        raise HTTPException(400, "unknown_sector")
    await resume_sector(sector)
    return {"ok": True, "sector": sector}


@app.get("/admin/publications")
async def list_publications(limit: int = 200) -> list[dict]:
    from src.publish.site import render_publications_latest
    return await render_publications_latest()


@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    return (
        "shitposter wire.\n"
        "GET  /stats              pipeline totals\n"
        "GET  /events.json        latest published events\n"
        "GET  /events/{id}        event detail\n"
        "GET  /rss                RSS feed\n"
        "GET  /metrics            Prometheus metrics\n"
        "GET  /admin/sources      source reputation table\n"
        "GET  /admin/circuit      sector circuit breaker status\n"
        "GET  /admin/budget       X write budget status\n"
        "GET  /admin/publications recent publications\n"
        "POST /admin/pause        trip global kill switch\n"
        "POST /admin/resume       lift global kill switch\n"
        "POST /admin/retract/{id} manually mark event retracted\n"
        "POST /admin/circuit/{sector}/resume  lift sector circuit breaker\n"
    )
