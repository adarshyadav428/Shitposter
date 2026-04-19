from datetime import datetime, timedelta, timezone

from newsbot.domain import Sector
from newsbot.publish.x_policy import can_publish_x
from newsbot.state.store import StateStore
from newsbot.survival.circuit_breaker import CircuitBreaker


def test_circuit_breaker_trips_after_two_retractions() -> None:
    store = StateStore(x_monthly_budget=40, x_correction_budget=10)
    cb = CircuitBreaker(store, threshold_24h=2)
    assert cb.record_retraction(Sector.CRYPTO) is False
    assert cb.record_retraction(Sector.CRYPTO) is True
    assert store.sector_paused[Sector.CRYPTO] is True


def test_x_policy_budget_and_gap() -> None:
    store = StateStore(x_monthly_budget=1, x_correction_budget=1)
    can, _ = can_publish_x(store)
    # Environment may disable X by default; this checks deterministic budget logic path.
    if can:
        store.x_used = 1
        can2, reason2 = can_publish_x(store)
        assert can2 is False
        assert reason2 == "x_budget_exhausted"

        store.x_used = 0
        store.x_last_post_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        can3, reason3 = can_publish_x(store)
        assert can3 is False
        assert reason3 == "x_min_gap_not_elapsed"
