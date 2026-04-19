from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from newsbot.domain import RawEvent, Sector, SourceTier, Witness
from newsbot.ingest.base import Ingestor, SourceSpec


class MockIngestor(Ingestor):
    def __init__(
        self,
        source_id: str,
        family: str,
        tier: SourceTier,
        sector: Sector,
        items: list[dict],
    ) -> None:
        self.spec = SourceSpec(
            source_id=source_id,
            source_family=family,
            tier=tier,
            sector_hint=sector.value,
        )
        self.sector = sector
        self.items = items

    async def poll(self) -> Iterable[RawEvent]:
        out: list[RawEvent] = []
        now = datetime.now(timezone.utc)
        for idx, item in enumerate(self.items):
            text = item.get("body", "")
            witness = Witness(
                source_id=self.spec.source_id,
                source_family=self.spec.source_family,
                source_tier=self.spec.tier,
                reputation=float(item.get("reputation", 0.9)),
                seen_at=now,
                url=item.get("url", "https://example.com"),
                text=text,
            )
            out.append(
                RawEvent(
                    event_id=f"{self.spec.source_id}-{idx}",
                    sector=self.sector,
                    headline=item["headline"],
                    body=text,
                    seen_at=now,
                    witness=witness,
                    entities=set(item.get("entities", [])),
                )
            )
        return out
