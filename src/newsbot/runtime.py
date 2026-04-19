from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime, timezone

from newsbot.config import settings
from newsbot.orchestrator import Orchestrator
from newsbot.state.persistence import save_state
from newsbot.telemetry import set_autopilot_running


class AutopilotRunner:
    def __init__(
        self,
        orchestrator: Orchestrator,
        poll_interval_seconds: int,
        snapshot_path: str | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.poll_interval_seconds = max(5, poll_interval_seconds)
        self.snapshot_path = snapshot_path
        self._task: asyncio.Task | None = None
        self._last_stats: dict[str, int] | None = None
        self._last_error: str | None = None
        self._last_run_at: datetime | None = None

    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> bool:
        if self.is_running():
            return False
        self._task = asyncio.create_task(self._loop(), name="newsbot-autopilot")
        set_autopilot_running(True)
        return True

    async def stop(self) -> bool:
        if self._task is None:
            return False
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        if self.snapshot_path:
            save_state(self.orchestrator.store, path_override=self.snapshot_path)
        self._task = None
        set_autopilot_running(False)
        return True

    async def run_once_now(self) -> dict[str, int]:
        stats = await self.orchestrator.run_once()
        if settings.retention_enabled:
            self.orchestrator.store.prune(
                max_events=settings.retention_max_events,
                max_publications=settings.retention_max_publications,
                max_failed_publications=settings.retention_max_failed_publications,
                max_drop_samples=settings.retention_max_drop_samples,
            )
        self._last_stats = stats
        self._last_error = None
        self._last_run_at = datetime.now(timezone.utc)
        if self.snapshot_path:
            save_state(self.orchestrator.store, path_override=self.snapshot_path)
        return stats

    def status(self) -> dict:
        return {
            "running": self.is_running(),
            "poll_interval_seconds": self.poll_interval_seconds,
            "last_stats": self._last_stats,
            "last_error": self._last_error,
            "last_run_at": self._last_run_at.isoformat() if self._last_run_at else None,
        }

    async def _loop(self) -> None:
        while True:
            try:
                await self.run_once_now()
            except Exception as exc:
                self._last_error = f"{type(exc).__name__}: {exc}"
                self._last_run_at = datetime.now(timezone.utc)
            await asyncio.sleep(self.poll_interval_seconds)
