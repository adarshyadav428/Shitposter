"""Connect bus stages to their handlers. Runs as asyncio tasks inside FastAPI."""
from __future__ import annotations

import asyncio

from src.ingest.base import Ingestor
from src.ingest.registry import build_fleet
from src.ingest.retraction_monitor import RetractionMonitor
from src.llm.compose_stage import handle_verified
from src.obs.logs import get_logger
from src.pipeline.cluster import handle_raw_event
from src.pipeline.verify import evaluate
from src.publish.fanout import Fanout
from src.survival.engagement import EngagementScheduler
from src.state.redis_bus import (
    STREAM_CLUSTERED,
    STREAM_COMPOSED,
    STREAM_RAW,
    STREAM_VERIFIED,
    ack,
    consume,
    kill_switch_engaged,
)

log = get_logger(__name__)


class Orchestrator:
    def __init__(self) -> None:
        self._tasks: list[asyncio.Task] = []
        self._fleet: list[Ingestor] = []
        self._fanout = Fanout()
        self._retraction_monitor = RetractionMonitor()
        self._engagement = EngagementScheduler()

    async def start(self) -> None:
        self._fleet = build_fleet()
        for ing in self._fleet:
            self._tasks.append(asyncio.create_task(ing.run(), name=f"ing:{ing.source_id}"))

        self._tasks.append(asyncio.create_task(self._cluster_loop(), name="cluster"))
        self._tasks.append(asyncio.create_task(self._verify_loop(), name="verify"))
        self._tasks.append(asyncio.create_task(self._compose_loop(), name="compose"))
        self._tasks.append(asyncio.create_task(self._publish_loop(), name="publish"))
        self._tasks.append(asyncio.create_task(self._retry_held_events(), name="held-sweeper"))
        self._tasks.append(
            asyncio.create_task(
                self._retraction_monitor.run_forever(), name="retraction-monitor"
            )
        )
        self._tasks.append(
            asyncio.create_task(self._engagement.run_forever(), name="engagement")
        )
        log.info("orchestrator.started", ingestors=len(self._fleet))

    async def stop(self) -> None:
        for ing in self._fleet:
            ing.stop()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        log.info("orchestrator.stopped")

    async def _cluster_loop(self) -> None:
        group = "cluster"
        async for msg_id, payload in consume(STREAM_RAW, group, "worker-1"):
            try:
                if await kill_switch_engaged():
                    await ack(STREAM_RAW, group, msg_id)
                    continue
                await handle_raw_event(payload)
            except Exception as exc:
                log.error("cluster.handler_err", err=str(exc))
            finally:
                await ack(STREAM_RAW, group, msg_id)

    async def _verify_loop(self) -> None:
        group = "verify"
        async for msg_id, payload in consume(STREAM_CLUSTERED, group, "worker-1"):
            try:
                await evaluate(payload["event_id"])
            except Exception as exc:
                log.error("verify.handler_err", err=str(exc))
            finally:
                await ack(STREAM_CLUSTERED, group, msg_id)

    async def _compose_loop(self) -> None:
        group = "compose"
        async for msg_id, payload in consume(STREAM_VERIFIED, group, "worker-1"):
            try:
                await handle_verified(payload["event_id"])
            except Exception as exc:
                log.error("compose.handler_err", err=str(exc))
            finally:
                await ack(STREAM_VERIFIED, group, msg_id)

    async def _publish_loop(self) -> None:
        group = "publish"
        async for msg_id, payload in consume(STREAM_COMPOSED, group, "worker-1"):
            try:
                await self._fanout.handle_composed(payload["event_id"])
            except Exception as exc:
                log.error("publish.handler_err", err=str(exc))
            finally:
                await ack(STREAM_COMPOSED, group, msg_id)

    async def _retry_held_events(self) -> None:
        """Re-run verify on 'held' events every 15s to catch the 90s window expiring."""
        from sqlalchemy import select

        from src.state.db import session_scope
        from src.state.models import CanonicalEvent

        while True:
            await asyncio.sleep(15)
            async with session_scope() as s:
                rows = (
                    await s.execute(
                        select(CanonicalEvent.id).where(CanonicalEvent.state == "held")
                    )
                ).all()
            for (eid,) in rows:
                try:
                    await evaluate(eid)
                except Exception as exc:
                    log.error("retry_held.err", err=str(exc), event_id=eid)
