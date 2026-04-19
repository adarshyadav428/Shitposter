"""Weekly retraction audit.  Run from cron: `0 9 * * 1 python -m scripts.retraction_audit`

Prints a report of:
- Total published events
- Total retracted events (and rate)
- Top 5 sources with worst retraction rates
- Any source on cooldown
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from src.obs.logs import configure_logging, get_logger
from src.state.db import session_scope
from src.state.models import CanonicalEvent, Source

log = get_logger(__name__)


async def run() -> None:
    configure_logging()
    cutoff = datetime.now(UTC) - timedelta(days=7)

    async with session_scope() as s:
        total_q = select(CanonicalEvent).where(CanonicalEvent.state.in_(["published", "retracted"]))
        all_events = (await s.execute(total_q)).scalars().all()

        recent_q = select(CanonicalEvent).where(
            CanonicalEvent.state.in_(["published", "retracted"]),
            CanonicalEvent.first_seen_at >= cutoff,
        )
        recent = (await s.execute(recent_q)).scalars().all()

        retracted_total = sum(1 for e in all_events if e.retracted)
        retracted_recent = sum(1 for e in recent if e.retracted)

        sources = (await s.execute(select(Source))).scalars().all()

    retraction_rate = retracted_total / max(len(all_events), 1) * 100
    recent_rate = retracted_recent / max(len(recent), 1) * 100

    print(f"\n{'='*60}")
    print(f"SHITPOSTER WEEKLY RETRACTION AUDIT — {datetime.now(UTC).date()}")
    print(f"{'='*60}")
    print(f"\nAll-time: {len(all_events)} events, {retracted_total} retracted ({retraction_rate:.1f}%)")
    print(f"Last 7d:  {len(recent)} events, {retracted_recent} retracted ({recent_rate:.1f}%)")

    # Source reputation table
    print(f"\n{'Source':<30} {'Tier':<5} {'Reputation':<12} {'Alpha':<8} {'Beta':<8} {'Cooldown'}")
    print("-" * 80)
    for src in sorted(sources, key=lambda s: s.reputation):
        cooldown = "YES" if (src.cooldown_until and datetime.now(UTC) < src.cooldown_until) else ""
        print(
            f"{src.id:<30} {src.tier:<5} {src.reputation:<12.4f} "
            f"{src.rep_alpha:<8.1f} {src.rep_beta:<8.1f} {cooldown}"
        )

    # Worst sources
    worst = sorted(
        [s for s in sources if s.rep_beta > 1.0],
        key=lambda s: s.rep_beta / max(s.rep_alpha, 0.001),
        reverse=True,
    )[:5]
    if worst:
        print(f"\nTop 5 sources by retraction ratio:")
        for src in worst:
            ratio = src.rep_beta / max(src.rep_alpha, 0.001)
            print(f"  {src.id}: beta/alpha ratio = {ratio:.3f}")

    on_cooldown = [s for s in sources if s.cooldown_until and datetime.now(UTC) < s.cooldown_until]
    if on_cooldown:
        print(f"\nSources on cooldown ({len(on_cooldown)}):")
        for src in on_cooldown:
            print(f"  {src.id}: until {src.cooldown_until}")
    print()


if __name__ == "__main__":
    asyncio.run(run())
