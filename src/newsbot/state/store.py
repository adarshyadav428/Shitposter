from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from newsbot.domain import CanonicalEvent, Sector


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
