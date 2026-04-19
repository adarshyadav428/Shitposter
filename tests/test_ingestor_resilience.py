import pytest

from newsbot.domain import Sector, SourceTier
from newsbot.ingest.base import Ingestor, SourceSpec
from newsbot.ingest.mock import MockIngestor
from newsbot.orchestrator import Orchestrator
from newsbot.publish.fanout import Fanout
from newsbot.state.store import StateStore


class FailingIngestor(Ingestor):
    spec = SourceSpec(
        source_id="failing-source",
        source_family="broken-family",
        tier=SourceTier.T2,
        sector_hint=Sector.CRYPTO.value,
    )

    async def poll(self):
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_orchestrator_survives_single_ingestor_failure() -> None:
    ok = MockIngestor(
        source_id="ok-source",
        family="ok-family",
        tier=SourceTier.T1,
        sector=Sector.MACRO,
        items=[
            {
                "headline": "Central bank emergency statement",
                "body": "Immediate policy action announced.",
                "entities": ["FED"],
                "url": "https://example.com/ok",
            }
        ],
    )
    fail = FailingIngestor()
    store = StateStore(x_monthly_budget=40, x_correction_budget=10)
    orchestrator = Orchestrator([fail, ok], store=store, fanout=Fanout(store))

    stats = await orchestrator.run_once()
    ingestor_stats = orchestrator.get_ingestor_stats()

    assert stats["raw"] >= 1
    assert stats["published"] >= 1
    assert int(ingestor_stats["failing-source"]["failed_polls"]) >= 1
    assert int(ingestor_stats["ok-source"]["ok_polls"]) >= 1
