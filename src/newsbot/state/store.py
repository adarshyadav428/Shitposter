from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from newsbot.domain import CanonicalEvent, Sector, SourceTier, Witness


@dataclass(slots=True)
class PublicationRecord:
    event_id: str
    channel: str
    created_at: datetime
    payload: str


class StateStore:
    def __init__(self, x_monthly_budget: int, x_correction_budget: int) -> None:
        self.events: dict[str, CanonicalEvent] = {}
        self.publications: list[PublicationRecord] = []
        self.retracted_event_ids: set[str] = set()
        self.global_pause: bool = False
        self.sector_paused: dict[Sector, bool] = defaultdict(bool)
        self.source_reputation: dict[str, float] = {}
        self.retraction_windows: dict[Sector, deque[datetime]] = defaultdict(deque)

        self.x_monthly_budget = x_monthly_budget
        self.x_correction_budget = x_correction_budget
        self.x_used = 0
        self.x_correction_used = 0
        self.x_last_post_at: datetime | None = None

    def add_event(self, event: CanonicalEvent) -> None:
        self.events[event.event_id] = event

    def get_event(self, event_id: str) -> CanonicalEvent | None:
        return self.events.get(event_id)

    def list_events(self) -> list[CanonicalEvent]:
        return sorted(self.events.values(), key=lambda e: e.updated_at, reverse=True)

    def add_publication(self, record: PublicationRecord) -> None:
        self.publications.append(record)

    def list_publications(self, limit: int = 100) -> list[PublicationRecord]:
        return self.publications[-limit:]

    def mark_retracted(self, event_id: str) -> None:
        self.retracted_event_ids.add(event_id)

    def is_retracted(self, event_id: str) -> bool:
        return event_id in self.retracted_event_ids

    def is_paused(self, sector: Sector) -> bool:
        return self.global_pause or self.sector_paused.get(sector, False)

    def register_retraction(self, sector: Sector, now: datetime) -> int:
        window = self.retraction_windows[sector]
        window.append(now)
        cutoff = now - timedelta(hours=24)
        while window and window[0] < cutoff:
            window.popleft()
        return len(window)

    def get_retraction_count_24h(self, sector: Sector, now: datetime | None = None) -> int:
        current = now or datetime.now(timezone.utc)
        window = self.retraction_windows[sector]
        cutoff = current - timedelta(hours=24)
        while window and window[0] < cutoff:
            window.popleft()
        return len(window)

    def to_dict(self) -> dict:
        return {
            "events": [self._event_to_dict(event) for event in self.events.values()],
            "publications": [
                {
                    "event_id": row.event_id,
                    "channel": row.channel,
                    "created_at": row.created_at.isoformat(),
                    "payload": row.payload,
                }
                for row in self.publications
            ],
            "retracted_event_ids": sorted(self.retracted_event_ids),
            "global_pause": self.global_pause,
            "sector_paused": {k.value: v for k, v in self.sector_paused.items()},
            "source_reputation": self.source_reputation,
            "retraction_windows": {
                sector.value: [item.isoformat() for item in values]
                for sector, values in self.retraction_windows.items()
            },
            "x_monthly_budget": self.x_monthly_budget,
            "x_correction_budget": self.x_correction_budget,
            "x_used": self.x_used,
            "x_correction_used": self.x_correction_used,
            "x_last_post_at": self.x_last_post_at.isoformat() if self.x_last_post_at else None,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "StateStore":
        store = cls(
            x_monthly_budget=int(payload.get("x_monthly_budget", 40)),
            x_correction_budget=int(payload.get("x_correction_budget", 10)),
        )
        store.global_pause = bool(payload.get("global_pause", False))

        for sector_name, value in payload.get("sector_paused", {}).items():
            store.sector_paused[Sector(sector_name)] = bool(value)

        store.source_reputation = {
            str(k): float(v) for k, v in payload.get("source_reputation", {}).items()
        }

        for sector_name, values in payload.get("retraction_windows", {}).items():
            sector = Sector(sector_name)
            parsed = deque(datetime.fromisoformat(item) for item in values)
            store.retraction_windows[sector] = parsed

        for row in payload.get("publications", []):
            store.publications.append(
                PublicationRecord(
                    event_id=row["event_id"],
                    channel=row["channel"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    payload=row["payload"],
                )
            )

        store.retracted_event_ids = set(payload.get("retracted_event_ids", []))

        for event in payload.get("events", []):
            built = cls._event_from_dict(event)
            store.events[built.event_id] = built

        store.x_used = int(payload.get("x_used", 0))
        store.x_correction_used = int(payload.get("x_correction_used", 0))
        x_last_post_at = payload.get("x_last_post_at")
        store.x_last_post_at = datetime.fromisoformat(x_last_post_at) if x_last_post_at else None
        return store

    @staticmethod
    def _event_to_dict(event: CanonicalEvent) -> dict:
        return {
            "event_id": event.event_id,
            "sector": event.sector.value,
            "headline": event.headline,
            "body": event.body,
            "first_seen_at": event.first_seen_at.isoformat(),
            "updated_at": event.updated_at.isoformat(),
            "entities": sorted(event.entities),
            "witnesses": [
                {
                    "source_id": witness.source_id,
                    "source_family": witness.source_family,
                    "source_tier": int(witness.source_tier),
                    "reputation": witness.reputation,
                    "seen_at": witness.seen_at.isoformat(),
                    "url": witness.url,
                    "text": witness.text,
                }
                for witness in event.witnesses
            ],
        }

    @staticmethod
    def _event_from_dict(payload: dict) -> CanonicalEvent:
        return CanonicalEvent(
            event_id=payload["event_id"],
            sector=Sector(payload["sector"]),
            headline=payload["headline"],
            body=payload["body"],
            first_seen_at=datetime.fromisoformat(payload["first_seen_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
            entities=set(payload.get("entities", [])),
            witnesses=[
                Witness(
                    source_id=item["source_id"],
                    source_family=item["source_family"],
                    source_tier=SourceTier(item["source_tier"]),
                    reputation=float(item["reputation"]),
                    seen_at=datetime.fromisoformat(item["seen_at"]),
                    url=item["url"],
                    text=item["text"],
                )
                for item in payload.get("witnesses", [])
            ],
        )
