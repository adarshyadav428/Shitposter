from __future__ import annotations

from datetime import datetime, timezone

from newsbot.config import settings
from newsbot.state.store import StateStore
from newsbot.survival.cadence import min_gap_elapsed
from newsbot.survival.warmup import account_is_warmed


def can_publish_x(store: StateStore) -> tuple[bool, str]:
    if not settings.x_enabled:
        return False, "x_disabled"
    if not account_is_warmed(settings.x_account_created_at):
        return False, "x_account_not_warmed"
    if store.x_used >= store.x_monthly_budget:
        return False, "x_budget_exhausted"

    now = datetime.now(timezone.utc)
    if store.x_last_post_at is not None:
        since = (now - store.x_last_post_at).total_seconds()
        if not min_gap_elapsed(since, settings.x_min_gap_minutes):
            return False, "x_min_gap_not_elapsed"

    return True, "ok"


def can_publish_x_correction(store: StateStore) -> tuple[bool, str]:
    if not settings.x_enabled:
        return False, "x_disabled"
    if store.x_correction_used >= store.x_correction_budget:
        return False, "x_correction_budget_exhausted"
    return True, "ok"
