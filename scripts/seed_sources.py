"""Populate the `sources` table so the verify stage knows tier/family/reputation."""
from __future__ import annotations

import asyncio

from sqlalchemy.dialects.postgresql import insert

from src.ingest.registry import build_fleet
from src.obs.logs import configure_logging, get_logger
from src.state.db import session_scope
from src.state.models import Source

log = get_logger(__name__)


async def main() -> None:
    configure_logging()
    fleet = build_fleet()
    async with session_scope() as s:
        for ing in fleet:
            stmt = (
                insert(Source)
                .values(
                    id=ing.source_id,
                    family=ing.source_family,
                    tier=int(ing.tier),
                    kind=ing.__class__.__name__,
                    url=getattr(ing, "url", ""),
                    sector=ing.sector,
                    rep_alpha=4.0,
                    rep_beta=1.0,
                    active=True,
                )
                .on_conflict_do_nothing(index_elements=["id"])
            )
            await s.execute(stmt)
    log.info("seed.done", count=len(fleet))


if __name__ == "__main__":
    asyncio.run(main())
