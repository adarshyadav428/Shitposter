"""Cron: one-shot retraction sweep (alternative to background RetractionMonitor).

Run as: `python -m scripts.retraction_sweep` or via crontab.
Useful if the main app is stopped and you want a standalone retraction check.

The live app uses src/ingest/retraction_monitor.py (continuous).
This script provides the same logic as a one-shot cron backup.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select

from src.obs.logs import configure_logging, get_logger
from src.publish.telegram_bot import TelegramPublisher
from src.state.circuit_breaker import record_sector_retraction
from src.state.db import session_scope
from src.state.models import CanonicalEvent, RawItem
from src.state.reputation import record_retraction

log = get_logger(__name__)
RETRACTION_KEYWORDS = ("correction", "retracted", "retraction", "updated headline")
LOOKBACK_HOURS = 24


async def main() -> None:
    configure_logging()
    tg = TelegramPublisher()
    async with session_scope() as s:
        q = select(CanonicalEvent).where(
            CanonicalEvent.state == "published",
            CanonicalEvent.retracted.is_(False),
            CanonicalEvent.last_seen_at >= datetime.now(UTC) - timedelta(hours=LOOKBACK_HOURS),
        )
        events = (await s.execute(q)).scalars().all()
        pairs: list[tuple[CanonicalEvent, list[RawItem]]] = []
        for ev in events:
            items = (
                await s.execute(select(RawItem).where(RawItem.canonical_event_id == ev.id))
            ).scalars().all()
            pairs.append((ev, list(items)))

    log.info("retraction_sweep.start", events=len(pairs))

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
        for ev, items in pairs:
            retract = False
            for item in items:
                if not item.url:
                    continue
                try:
                    resp = await c.get(item.url)
                except httpx.HTTPError:
                    continue
                if resp.status_code in (404, 410):
                    retract = True
                    break
                low = resp.text[:5_000].lower()
                if any(k in low for k in RETRACTION_KEYWORDS):
                    retract = True
                    break
            if not retract:
                continue

            async with session_scope() as s:
                fresh = await s.get(CanonicalEvent, ev.id)
                if fresh is None or fresh.retracted:
                    continue
                fresh.retracted = True
                fresh.retracted_at = datetime.now(UTC)

            for item in items:
                await record_retraction(item.source_id)
            await record_sector_retraction(ev.sector)

            await tg.publish_correction(ev.draft or ev.title, "Source appears retracted.")
            log.info("retraction_sweep.flagged", event_id=ev.id, sector=ev.sector)

    log.info("retraction_sweep.done")


if __name__ == "__main__":
    asyncio.run(main())
