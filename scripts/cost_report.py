"""Monthly Anthropic API cost estimator.

Queries the Anthropic usage API (if available) or estimates from local metrics.
Prints a breakdown by model and a projection for the rest of the month.

Usage: `python -m scripts.cost_report`
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from src.obs.logs import configure_logging, get_logger
from src.state.db import session_scope
from src.state.models import CanonicalEvent

log = get_logger(__name__)

# Approximate costs (USD per 1M tokens) as of early 2026
COST_PER_MILLION: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_read": 0.30},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0, "cache_read": 0.08},
}

# Rough token estimates per pipeline event
TOKENS_PER_EVENT = {
    "claims_input": 1_500,    # Haiku: source text -> claims
    "claims_output": 300,
    "compose_input": 2_000,   # Sonnet: source + claims -> draft (mostly cached)
    "compose_output": 100,
    "compose_cache_read": 1_800,  # system prompt read from cache
    "judge_input": 2_500,     # Haiku: claims + source + draft
    "judge_output": 150,
}


async def run() -> None:
    configure_logging()
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    async with session_scope() as s:
        composed_this_month = (
            await s.execute(
                select(func.count(CanonicalEvent.id)).where(
                    CanonicalEvent.state.in_(["composed", "published"]),
                    CanonicalEvent.first_seen_at >= month_start,
                )
            )
        ).scalar() or 0

    days_elapsed = max((now - month_start).days, 1)
    days_in_month = 30
    projection = int(composed_this_month / days_elapsed * days_in_month)

    haiku_cost = COST_PER_MILLION["claude-haiku-4-5-20251001"]
    sonnet_cost = COST_PER_MILLION["claude-sonnet-4-6"]

    def haiku_per_event() -> float:
        inp = (TOKENS_PER_EVENT["claims_input"] + TOKENS_PER_EVENT["judge_input"]) / 1e6 * haiku_cost["input"]
        out = (TOKENS_PER_EVENT["claims_output"] + TOKENS_PER_EVENT["judge_output"]) / 1e6 * haiku_cost["output"]
        return inp + out

    def sonnet_per_event() -> float:
        inp = TOKENS_PER_EVENT["compose_input"] / 1e6 * sonnet_cost["input"]
        out = TOKENS_PER_EVENT["compose_output"] / 1e6 * sonnet_cost["output"]
        cache = TOKENS_PER_EVENT["compose_cache_read"] / 1e6 * sonnet_cost["cache_read"]
        return inp + out + cache

    cost_per_event = haiku_per_event() + sonnet_per_event()
    actual_cost = composed_this_month * cost_per_event
    projected_cost = projection * cost_per_event

    print(f"\n{'='*60}")
    print(f"SHITPOSTER ANTHROPIC COST REPORT — {now.strftime('%Y-%m')}")
    print(f"{'='*60}")
    print(f"\nEvents composed (MTD):  {composed_this_month:,}")
    print(f"Days elapsed:           {days_elapsed}/{days_in_month}")
    print(f"Projected (full month): {projection:,} events")
    print(f"\nCost per event:         ${cost_per_event:.5f}")
    print(f"  Haiku (claims+judge): ${haiku_per_event():.5f}")
    print(f"  Sonnet (compose):     ${sonnet_per_event():.5f}")
    print(f"\nActual MTD cost:        ${actual_cost:.2f}")
    print(f"Projected month cost:   ${projected_cost:.2f}")
    print(f"\nNote: these are estimates. Actual costs depend on prompt caching hit")
    print(f"rate and exact token counts. Check console.anthropic.com for actuals.")
    print()


if __name__ == "__main__":
    asyncio.run(run())
