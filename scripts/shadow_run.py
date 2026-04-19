"""Shadow mode: run the full pipeline but block the X publisher.

Flip ENV=shadow in .env and the X publisher will refuse via kill-switch.
This script just engages the kill switch and confirms state.
"""
from __future__ import annotations

import asyncio

from src.config import get_settings
from src.state.redis_bus import client


async def main() -> None:
    settings = get_settings()
    r = client()
    await r.set(settings.kill_switch_key, "1")
    val = await r.get(settings.kill_switch_key)
    print(f"kill switch engaged: {val!r}")
    print("Telegram, Bluesky, Mastodon, and site will still publish.")
    print("Run `curl -XPOST http://localhost:8000/admin/resume` to lift.")


if __name__ == "__main__":
    asyncio.run(main())
