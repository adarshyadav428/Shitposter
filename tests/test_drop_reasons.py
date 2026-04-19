import pytest

from newsbot.domain import Sector, SourceTier
from newsbot.ingest.mock import MockIngestor
from newsbot.orchestrator import Orchestrator
from newsbot.publish.fanout import Fanout
from newsbot.state.store import StateStore


@pytest.mark.asyncio
async def test_dedupe_drop_reason_is_recorded() -> None:
    ingestor = MockIngestor(
        source_id="dup-source",
        family="dup-family",
        tier=SourceTier.T2,
        sector=Sector.CRYPTO,
        items=[
            {
                "headline": "Exchange incident update",
                "body": "Withdrawals paused due to infra issue.",
                "entities": ["BTC"],
                "url": "https://example.com/a",
            },
            {
                "headline": "Exchange incident update",
                "body": "Withdrawals paused due to infra issue.",
                "entities": ["BTC"],
                "url": "https://example.com/b",
            },
        ],
    )
    store = StateStore(x_monthly_budget=40, x_correction_budget=10)
    orchestrator = Orchestrator([ingestor], store=store, fanout=Fanout(store))

    await orchestrator.run_once()
    counts = store.get_drop_reason_counts()

    assert counts.get("dedupe_duplicate", 0) >= 1
    samples = store.list_drop_samples(limit=10)
    assert any(item["reason"] == "dedupe_duplicate" for item in samples)
