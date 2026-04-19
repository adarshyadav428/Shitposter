from __future__ import annotations

import asyncio

from newsbot.config import settings
from newsbot.orchestrator import Orchestrator
from newsbot.publish.fanout import Fanout
from newsbot.source_registry import build_ingestor_fleet
from newsbot.state.persistence import load_state
from newsbot.state.store import StateStore


def build_default_orchestrator() -> Orchestrator:
    store = None
    if settings.enable_state_snapshot:
        store = load_state()
    if store is None:
        store = StateStore(
            x_monthly_budget=settings.x_monthly_budget,
            x_correction_budget=settings.x_correction_budget,
        )
    fanout = Fanout(store=store)
    ingestors = build_ingestor_fleet()
    return Orchestrator(ingestors=ingestors, store=store, fanout=fanout)


async def _run_forever() -> None:
    orchestrator = build_default_orchestrator()
    while True:
        stats = await orchestrator.run_once()
        print(stats)
        await asyncio.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(_run_forever())
