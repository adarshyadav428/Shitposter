from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime, timezone
from typing import Awaitable, Callable

from newsbot.config import settings
from newsbot.publish.channels import TelegramPublisher
from newsbot.telemetry import observe_heartbeat_failure, set_heartbeat_running

HeartbeatSender = Callable[[str], Awaitable[str]]


class HeartbeatRunner:
    def __init__(self, interval_seconds: int = 300, sender: HeartbeatSender | None = None) -> None:
        self.interval_seconds = max(30, interval_seconds)
        self.sender = sender or self._default_sender
        self._task: asyncio.Task | None = None
        self._last_sent_at: datetime | None = None
        self._last_error: str | None = None

    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> bool:
        if self.is_running():
            return False
        self._task = asyncio.create_task(self._loop(), name="newsbot-heartbeat")
        set_heartbeat_running(True)
        return True

    async def stop(self) -> bool:
        if self._task is None:
            return False
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        set_heartbeat_running(False)
        return True

    async def send_once(self) -> bool:
        try:
            now = datetime.now(timezone.utc)
            message = f"newsbot heartbeat ok {now.isoformat()}"
            await self.sender(message)
            self._last_sent_at = now
            self._last_error = None
            return True
        except Exception as exc:
            self._last_error = f"{type(exc).__name__}: {exc}"
            observe_heartbeat_failure()
            return False

    def status(self) -> dict:
        return {
            "running": self.is_running(),
            "interval_seconds": self.interval_seconds,
            "last_sent_at": self._last_sent_at.isoformat() if self._last_sent_at else None,
            "last_error": self._last_error,
        }

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(self.interval_seconds)
            await self.send_once()

    @staticmethod
    async def _default_sender(message: str) -> str:
        if not (
            settings.telegram_enabled
            and settings.telegram_bot_token
            and settings.telegram_chat_id
        ):
            return "heartbeat:noop"
        publisher = TelegramPublisher(settings.telegram_bot_token, settings.telegram_chat_id)
        return await publisher.publish(message)
