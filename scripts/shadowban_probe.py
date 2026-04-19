"""Run this from cron nightly for each publishing handle."""
from __future__ import annotations

import asyncio
import sys

from src.obs.logs import configure_logging
from src.survival.shadowban import auto_pause_if_shadowbanned


async def main(handle: str) -> None:
    configure_logging()
    await auto_pause_if_shadowbanned(handle)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
