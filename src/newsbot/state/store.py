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


@dataclass(slots=True)
class FailedPublicationRecord:
    event_id: str
    channel: str
    created_at: datetime
    payload: str
    error: str


class StateStore:
    def __init__(self, x_monthly_budget: int, x_correction_budget: int) -> None:
        self.events: dict[str, CanonicalEvent] = {}
        self.publications: list[PublicationRecord] = []
        self.failed_publications: list[FailedPublicationRecord] = []
        self.published_event_ids: set[str] = set()
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

    def add_failed_publication(self, record: FailedPublicationRecord) -> None:
        self.failed_publications.append(record)

    def list_failed_publications(self, limit: int = 100) -> list[FailedPublicationRecord]:
        return self.failed_publications[-limit:]

    def mark_published(self, event_id: str) -> None:
        self.published_event_ids.add(event_id)

    def is_published(self, event_id: str) -> bool:
        return event_id in self.published_event_ids

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

    def prune(
        self,
        max_events: int,
        max_publications: int,
        max_failed_publications: int,
    ) -> dict[str, int]:
        removed_events = 0
        if max_events >= 0 and len(self.events) > max_events:
            ordered = sorted(self.events.values(), key=lambda e: e.updated_at, reverse=True)
            keep_ids = {event.event_id for event in ordered[:max_events]}
            for event_id in list(self.events.keys()):
                if event_id not in keep_ids:
                    del self.events[event_id]
                    removed_events += 1

            self.published_event_ids.intersection_update(self.events.keys())
            self.retracted_event_ids.intersection_update(self.events.keys())

        removed_publications = 0
        if max_publications >= 0 and len(self.publications) > max_publications:
            removed_publications = len(self.publications) - max_publications
            self.publications = self.publications[-max_publications:]

        removed_failed_publications = 0
        if max_failed_publications >= 0 and len(self.failed_publications) > max_failed_publications:
            removed_failed_publications = len(self.failed_publications) - max_failed_publications
            self.failed_publications = self.failed_publications[-max_failed_publications:]

        return {
            "removed_events": removed_events,
            "removed_publications": removed_publications,
            "removed_failed_publications": removed_failed_publications,
        }

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
            "failed_publications": [
                {
                    "event_id": row.event_id,
                    "channel": row.channel,
                    "created_at": row.created_at.isoformat(),
                    "payload": row.payload,
                    "error": row.error,
                }
                for row in self.failed_publications
            ],
            "published_event_ids": sorted(self.published_event_ids),
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

        for row in payload.get("failed_publications", []):
            store.failed_publications.append(
                FailedPublicationRecord(
                    event_id=row["event_id"],
                    channel=row["channel"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    payload=row["payload"],
                    error=row["error"],
                )
            )

        store.published_event_ids = set(payload.get("published_event_ids", []))
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
