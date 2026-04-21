from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


async def async_retry(
    operation: Callable[[], Awaitable],
    attempts: int = 3,
    initial_delay: float = 0.5,
    max_delay: float = 4.0,
    retriable_exceptions: tuple[type[BaseException], ...] = (Exception,),
):
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    delay = max(0.0, initial_delay)
    last_error: BaseException | None = None
    for idx in range(attempts):
        try:
            return await operation()
        except retriable_exceptions as exc:
            last_error = exc
            if idx == attempts - 1:
                break
            await asyncio.sleep(delay)
            delay = min(max_delay, max(delay * 2.0, 0.05))

    if last_error is not None:
        raise last_error
    raise RuntimeError("retry_failed_without_exception")
