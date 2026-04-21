import pytest

from newsbot.utils.retry import async_retry


@pytest.mark.asyncio
async def test_async_retry_succeeds_after_transient_failures() -> None:
    attempts = {"n": 0}

    async def op() -> str:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("temporary")
        return "ok"

    result = await async_retry(op, attempts=3, initial_delay=0.0, max_delay=0.0)
    assert result == "ok"
    assert attempts["n"] == 3


@pytest.mark.asyncio
async def test_async_retry_raises_after_attempt_budget() -> None:
    attempts = {"n": 0}

    async def op() -> str:
        attempts["n"] += 1
        raise RuntimeError("still broken")

    with pytest.raises(RuntimeError):
        await async_retry(op, attempts=2, initial_delay=0.0, max_delay=0.0)
    assert attempts["n"] == 2
