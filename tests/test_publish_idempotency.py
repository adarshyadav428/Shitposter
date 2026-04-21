from datetime import datetime, timezone

import pytest

from newsbot.domain import RawEvent, Sector, SourceTier, Witness
from newsbot.ingest.base import Ingestor, SourceSpec
from newsbot.orchestrator import Orchestrator
from newsbot.pipeline.dedupe import DedupeIndex
from newsbot.publish.fanout import Fanout
from newsbot.state.store import StateStore


class SequencedIngestor(Ingestor):
    spec = SourceSpec(
        source_id="seq-t1",
        source_family="seq-family",
        tier=SourceTier.T1,
        sector_hint=Sector.MACRO.value,
    )

    def __init__(self) -> None:
        self.i = 0

    async def poll(self):
        self.i += 1
        now = datetime.now(timezone.utc)
        witness = Witness(
            source_id=self.spec.source_id,
            source_family=self.spec.source_family,
            source_tier=self.spec.tier,
            reputation=0.9,
            seen_at=now,
            url=f"https://example.com/{self.i}",
            text=f"source payload nonce {self.i}",
        )
        headline = f"Macro emergency decision anchor text {self.i}"
        return [
            RawEvent(
                event_id=f"seq-{self.i}",
                sector=Sector.MACRO,
                headline=headline,
                body=f"Body nonce {self.i}",
                seen_at=now,
                witness=witness,
                entities={"FED"},
            )
        ]


@pytest.mark.asyncio
async def test_canonical_event_is_not_republished() -> None:
    ingestor = SequencedIngestor()
    store = StateStore(x_monthly_budget=40, x_correction_budget=10)
    orchestrator = Orchestrator(
        ingestors=[ingestor],
        store=store,
        fanout=Fanout(store=store),
        dedupe=DedupeIndex(max_distance=-1),
    )

    first = await orchestrator.run_once()
    pubs_after_first = len(store.publications)
    second = await orchestrator.run_once()
    pubs_after_second = len(store.publications)

    assert first["published"] >= 1
    assert second["published"] == 0
    assert pubs_after_second == pubs_after_first
