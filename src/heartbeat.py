"""Posts a private Telegram heartbeat every 5 minutes so silence != failure."""
from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from src.obs.logs import get_logger
from src.publish.telegram_bot import HeartbeatPublisher
from src.state.db import session_scope
from src.state.models import CanonicalEvent, Publication

log = get_logger(__name__)
INTERVAL_SECONDS = 300


async def run_forever() -> None:
    hb = HeartbeatPublisher()
    while True:
        try:
            async with session_scope() as s:
                total = (
                    await s.execute(select(func.count(CanonicalEvent.id)))
                ).scalar() or 0
                published = (
                    await s.execute(
                        select(func.count(Publication.id)).where(Publication.channel == "x")
                    )
                ).scalar() or 0
            await hb.publish(
                f"\u2713 ok events={total} x_posts={published}"
            )
        except Exception as exc:
            log.warning("heartbeat.err", err=str(exc))
        await asyncio.sleep(INTERVAL_SECONDS)
