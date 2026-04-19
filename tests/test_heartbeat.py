import pytest

from newsbot.heartbeat import HeartbeatRunner


@pytest.mark.asyncio
async def test_heartbeat_send_once_success() -> None:
    async def sender(_message: str) -> str:
        return "ok"

    runner = HeartbeatRunner(interval_seconds=60, sender=sender)
    sent = await runner.send_once()
    assert sent is True
    assert runner.status()["last_sent_at"] is not None


@pytest.mark.asyncio
async def test_heartbeat_send_once_failure() -> None:
    async def sender(_message: str) -> str:
        raise RuntimeError("send failed")

    runner = HeartbeatRunner(interval_seconds=60, sender=sender)
    sent = await runner.send_once()
    assert sent is False
    assert "RuntimeError" in (runner.status()["last_error"] or "")
