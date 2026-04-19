from __future__ import annotations

from datetime import timedelta

from newsbot.domain import CanonicalEvent, RawEvent


class ClusterEngine:
    def __init__(self, window_seconds: int = 900) -> None:
        self.window = timedelta(seconds=window_seconds)

    def assign(self, event: RawEvent, existing: list[CanonicalEvent]) -> CanonicalEvent:
        for candidate in existing:
            if candidate.sector != event.sector:
                continue
            if event.seen_at - candidate.updated_at > self.window:
                continue
            overlap = len(candidate.entities.intersection(event.entities))
            if overlap >= 1 or candidate.headline[:40] == event.headline[:40]:
                if len(event.headline) > len(candidate.headline):
                    candidate.headline = event.headline
                if len(event.body) > len(candidate.body):
                    candidate.body = event.body
                candidate.entities.update(event.entities)
                candidate.add_witness(event.witness)
                return candidate

        created = CanonicalEvent(
            event_id=event.event_id,
            sector=event.sector,
            headline=event.headline,
            body=event.body,
            first_seen_at=event.seen_at,
            updated_at=event.seen_at,
            entities=set(event.entities),
            witnesses=[event.witness],
        )
        return created
