from __future__ import annotations

import asyncio

from newsbot.config import settings
from newsbot.domain import Sector, SourceTier
from newsbot.ingest.mock import MockIngestor
from newsbot.orchestrator import Orchestrator
from newsbot.publish.fanout import Fanout
from newsbot.state.store import StateStore


def build_default_orchestrator() -> Orchestrator:
    store = StateStore(
        x_monthly_budget=settings.x_monthly_budget,
        x_correction_budget=settings.x_correction_budget,
    )
    fanout = Fanout(store=store)
    ingestors = [
        MockIngestor(
            source_id="sec-edgar",
            family="sec",
            tier=SourceTier.T1,
            sector=Sector.MACRO,
            items=[
                {
                    "headline": "Federal Reserve announces emergency liquidity operation",
                    "body": "The operation size is 50 billion and starts immediately.",
                    "entities": ["FED", "USD"],
                    "url": "https://example.com/fed",
                }
            ],
        ),
        MockIngestor(
            source_id="nitter-journalist-1",
            family="independent-journalist",
            tier=SourceTier.T2,
            sector=Sector.CRYPTO,
            items=[
                {
                    "headline": "Major exchange pauses withdrawals for BTC and ETH",
                    "body": "Exchange statement cites infrastructure incident.",
                    "entities": ["BTC", "ETH"],
                    "url": "https://example.com/exchange",
                }
            ],
        ),
    ]
    return Orchestrator(ingestors=ingestors, store=store, fanout=fanout)


async def _run_forever() -> None:
    orchestrator = build_default_orchestrator()
    while True:
        stats = await orchestrator.run_once()
        print(stats)
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(_run_forever())
