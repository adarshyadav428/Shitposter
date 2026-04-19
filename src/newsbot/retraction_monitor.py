from __future__ import annotations

import asyncio
import contextlib
import hashlib
from datetime import datetime, timezone
from typing import Awaitable, Callable

import httpx

from newsbot.orchestrator import Orchestrator

Fetcher = Callable[[str], Awaitable[str | None]]


class RetractionMonitor:
    def __init__(
        self,
        orchestrator: Orchestrator,
        interval_seconds: int = 300,
        fetcher: Fetcher | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.interval_seconds = max(30, interval_seconds)
        self.fetcher = fetcher or self._default_fetcher
        self._task: asyncio.Task | None = None
        self._last_scan_at: datetime | None = None
        self._last_error: str | None = None
        self._last_trigger_count: int = 0
        self._signatures: dict[str, str] = {}
        self._keywords = ("correction", "retraction", "withdrawn", "updated", "clarification")

    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> bool:
        if self.is_running():
            return False
        self._task = asyncio.create_task(self._loop(), name="newsbot-retraction-monitor")
        return True

    async def stop(self) -> bool:
        if self._task is None:
            return False
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        return True

    def status(self) -> dict:
        return {
            "running": self.is_running(),
            "interval_seconds": self.interval_seconds,
            "last_scan_at": self._last_scan_at.isoformat() if self._last_scan_at else None,
            "last_error": self._last_error,
            "last_trigger_count": self._last_trigger_count,
        }

    async def scan_once(self) -> int:
        triggered = 0
        for event in self.orchestrator.store.list_events():
            if self.orchestrator.store.is_retracted(event.event_id):
                continue
            if not event.witnesses:
                continue

            source_url = event.witnesses[0].url
            text = await self.fetcher(source_url)
            if not text:
                continue

            normalized = " ".join(text.lower().split())[:4000]
            signature = hashlib.sha1(normalized.encode()).hexdigest()
            previous = self._signatures.get(event.event_id)
            self._signatures[event.event_id] = signature
            if previous is None or previous == signature:
                continue

            if any(keyword in normalized for keyword in self._keywords):
                was_retracted = self.orchestrator.store.is_retracted(event.event_id)
                await self.orchestrator.retract(
                    event.event_id,
                    "source content changed and includes correction/retraction signal",
                )
                is_retracted = self.orchestrator.store.is_retracted(event.event_id)
                if is_retracted and not was_retracted:
                    triggered += 1

        self._last_scan_at = datetime.now(timezone.utc)
        self._last_trigger_count = triggered
        self._last_error = None
        return triggered

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(self.interval_seconds)
            try:
                await self.scan_once()
            except Exception as exc:
                self._last_error = f"{type(exc).__name__}: {exc}"
                self._last_scan_at = datetime.now(timezone.utc)

    @staticmethod
    async def _default_fetcher(url: str) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url)
            if response.status_code >= 400:
                return None
            return response.text
        except Exception:
            return None
