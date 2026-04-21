from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Iterable

import aiohttp
import feedparser

from newsbot.domain import RawEvent, Sector, Witness
from newsbot.ingest.base import Ingestor, SourceSpec
from newsbot.utils.retry import async_retry


class RSSIngestor(Ingestor):
    def __init__(self, spec: SourceSpec, feed_url: str, sector: Sector) -> None:
        self.spec = spec
        self.feed_url = feed_url
        self.sector = sector

    async def poll(self) -> Iterable[RawEvent]:
        timeout = aiohttp.ClientTimeout(total=10)
        headers = {"User-Agent": "newsbot/1.0 (+https://github.com/adarshyadav428/Shitposter)"}

        async def _fetch_payload() -> bytes:
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(self.feed_url) as response:
                    if response.status >= 400:
                        raise RuntimeError(f"rss_http_{response.status}")
                    return await response.read()

        try:
            payload = await async_retry(_fetch_payload, attempts=3, initial_delay=0.25)
        except Exception:
            return []

        parsed = feedparser.parse(payload)
        if getattr(parsed, "bozo", False) and not parsed.entries:
            return []

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
