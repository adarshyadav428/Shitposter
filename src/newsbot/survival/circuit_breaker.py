from datetime import datetime, timezone

from newsbot.domain import Sector
from newsbot.state.store import StateStore


class CircuitBreaker:
    def __init__(self, store: StateStore, threshold_24h: int = 2) -> None:
        self.store = store
        self.threshold_24h = threshold_24h

    def record_retraction(self, sector: Sector) -> bool:
        count = self.store.register_retraction(sector=sector, now=datetime.now(timezone.utc))
        if count >= self.threshold_24h:
            self.store.sector_paused[sector] = True
            return True
        return False

    def status(self) -> dict[str, dict[str, int | bool]]:
        now = datetime.now(timezone.utc)
        out: dict[str, dict[str, int | bool]] = {}
        for sector in Sector:
            out[sector.value] = {
                "paused": self.store.sector_paused.get(sector, False),
                "retractions_24h": self.store.get_retraction_count_24h(sector, now),
            }
        return out
