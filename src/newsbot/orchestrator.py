from __future__ import annotations

from collections import defaultdict

from newsbot.domain import CanonicalEvent, RawEvent
from newsbot.ingest.base import Ingestor
from newsbot.llm.claims import extract_claims
from newsbot.llm.judge import judge_draft
from newsbot.llm.summarize import compose_post
from newsbot.pipeline.cluster import ClusterEngine
from newsbot.pipeline.dedupe import DedupeIndex
from newsbot.pipeline.verify import VerifyEngine
from newsbot.publish.fanout import Fanout
from newsbot.state.store import StateStore
from newsbot.survival.circuit_breaker import CircuitBreaker


class Orchestrator:
    def __init__(
        self,
        ingestors: list[Ingestor],
        store: StateStore,
        fanout: Fanout,
        dedupe: DedupeIndex | None = None,
        cluster: ClusterEngine | None = None,
        verify: VerifyEngine | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self.ingestors = ingestors
        self.store = store
        self.fanout = fanout
        self.dedupe = dedupe or DedupeIndex()
        self.cluster = cluster or ClusterEngine()
        self.verify = verify or VerifyEngine()
        self.circuit_breaker = circuit_breaker or CircuitBreaker(store)

    async def run_once(self) -> dict[str, int]:
        raw_events: list[RawEvent] = []
        for ingestor in self.ingestors:
            fetched = await ingestor.poll()
            raw_events.extend(fetched)

        accepted = 0
        published = 0
        dropped = 0

        by_sector: dict[str, list[CanonicalEvent]] = defaultdict(list)
        for event in self.store.list_events():
            by_sector[event.sector.value].append(event)

        for event in raw_events:
            if self.store.is_paused(event.sector):
                dropped += 1
                continue
            if self.dedupe.seen_duplicate(event):
                dropped += 1
                continue

            existing = by_sector[event.sector.value]
            canonical = self.cluster.assign(event, existing)
            if canonical.event_id not in self.store.events:
                self.store.add_event(canonical)
                by_sector[event.sector.value].append(canonical)
            accepted += 1

            verdict = self.verify.evaluate(canonical)
            if not verdict.publish:
                continue

            claims = extract_claims(canonical)
            draft = compose_post(claims)
            ok, _reason = judge_draft(draft, claims)
            if not ok:
                dropped += 1
                continue

            await self.fanout.publish(canonical.event_id, draft)
            published += 1

        return {
            "raw": len(raw_events),
            "accepted": accepted,
            "published": published,
            "dropped": dropped,
        }

    async def retract(self, event_id: str, reason: str) -> bool:
        event = self.store.get_event(event_id)
        if event is None:
            return False
        triggered = self.circuit_breaker.record_retraction(event.sector)
        await self.fanout.publish_correction(event_id, reason)
        return triggered
