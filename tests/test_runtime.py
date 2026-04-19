import asyncio

import pytest

from newsbot.main import build_default_orchestrator
from newsbot.runtime import AutopilotRunner


@pytest.mark.asyncio
async def test_runner_start_stop() -> None:
    runner = AutopilotRunner(build_default_orchestrator(), poll_interval_seconds=5)
    started = await runner.start()
    assert started is True
    assert runner.is_running() is True

    await asyncio.sleep(0.1)
    status = runner.status()
    assert status["running"] is True

    stopped = await runner.stop()
    assert stopped is True
    assert runner.is_running() is False


@pytest.mark.asyncio
async def test_runner_run_once_now_updates_status() -> None:
    runner = AutopilotRunner(build_default_orchestrator(), poll_interval_seconds=5)
    stats = await runner.run_once_now()
    assert stats["raw"] >= 1
    assert runner.status()["last_run_at"] is not None


@pytest.mark.asyncio
async def test_runner_writes_snapshot(tmp_path) -> None:
    snapshot_path = tmp_path / "runner-state.json"
    runner = AutopilotRunner(
        build_default_orchestrator(),
        poll_interval_seconds=5,
        snapshot_path=str(snapshot_path),
    )
    await runner.run_once_now()
    assert snapshot_path.exists() is True
