from __future__ import annotations

import asyncio

from newsbot.main import build_default_orchestrator


async def main() -> None:
    orchestrator = build_default_orchestrator()
    totals = {"raw": 0, "accepted": 0, "published": 0, "dropped": 0}
    for _ in range(5):
        stats = await orchestrator.run_once()
        for k, v in stats.items():
            totals[k] += v
    print(totals)


if __name__ == "__main__":
    asyncio.run(main())
