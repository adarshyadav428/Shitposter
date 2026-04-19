from __future__ import annotations

import asyncio

from newsbot.main import build_default_orchestrator


async def main() -> None:
    orchestrator = build_default_orchestrator()
    stats = await orchestrator.run_once()
    print("shadow run stats", stats)
    for publication in orchestrator.store.list_publications(20):
        print(publication.channel, publication.payload[:120])


if __name__ == "__main__":
    asyncio.run(main())
