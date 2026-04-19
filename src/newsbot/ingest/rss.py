from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Iterable

import feedparser

from newsbot.domain import RawEvent, Sector, Witness
from newsbot.ingest.base import Ingestor, SourceSpec


class RSSIngestor(Ingestor):
    def __init__(self, spec: SourceSpec, feed_url: str, sector: Sector) -> None:
        self.spec = spec
        self.feed_url = feed_url
        self.sector = sector

    async def poll(self) -> Iterable[RawEvent]:
        parsed = feedparser.parse(self.feed_url)
        events: list[RawEvent] = []
        now = datetime.now(timezone.utc)
        for entry in parsed.entries[:10]:
            title = getattr(entry, "title", "").strip()
            summary = getattr(entry, "summary", "").strip()
            link = getattr(entry, "link", self.feed_url)
            if not title:
                continue
            base = f"{self.spec.source_id}:{title}:{link}".encode()
            fingerprint = hashlib.sha1(base).hexdigest()[:16]
            witness = Witness(
                source_id=self.spec.source_id,
                source_family=self.spec.source_family,
                source_tier=self.spec.tier,
                reputation=0.9,
                seen_at=now,
                url=link,
                text=f"{title}\n{summary}",
            )
            entities = {part.upper() for part in title.split() if part.isupper() and len(part) <= 6}
            events.append(
                RawEvent(
                    event_id=f"{self.spec.source_id}-{fingerprint}",
                    sector=self.sector,
                    headline=title,
                    body=summary,
                    seen_at=now,
                    witness=witness,
                    entities=entities,
                )
            )
        return events
