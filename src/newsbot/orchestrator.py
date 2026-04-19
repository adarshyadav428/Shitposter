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
from newsbot.state.reputation import ReputationModel
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
        reputation_model: ReputationModel | None = None,
    ) -> None:
        self.ingestors = ingestors
        self.store = store
        self.fanout = fanout
        self.dedupe = dedupe or DedupeIndex()
        self.cluster = cluster or ClusterEngine()
        self.verify = verify or VerifyEngine()
        self.circuit_breaker = circuit_breaker or CircuitBreaker(store)
        self.reputation_model = reputation_model or ReputationModel()
        self.ingestor_stats: dict[str, dict[str, int | str | None]] = {
            ingestor.spec.source_id: {
                "ok_polls": 0,
                "failed_polls": 0,
                "last_error": None,
                "last_event_count": 0,
            }
            for ingestor in ingestors
        }

    async def run_once(self) -> dict[str, int]:
        raw_events: list[RawEvent] = []
        for ingestor in self.ingestors:
            source_id = ingestor.spec.source_id
            try:
                fetched = await ingestor.poll()
                items = list(fetched)
                raw_events.extend(items)
                self.ingestor_stats[source_id]["ok_polls"] = int(
                    self.ingestor_stats[source_id]["ok_polls"]
                ) + 1
                self.ingestor_stats[source_id]["last_event_count"] = len(items)
                self.ingestor_stats[source_id]["last_error"] = None
            except Exception as exc:
                self.ingestor_stats[source_id]["failed_polls"] = int(
                    self.ingestor_stats[source_id]["failed_polls"]
                ) + 1
                self.ingestor_stats[source_id]["last_error"] = f"{type(exc).__name__}: {exc}"
                self.ingestor_stats[source_id]["last_event_count"] = 0

        accepted = 0
        published = 0
        dropped = 0

        by_sector: dict[str, list[CanonicalEvent]] = defaultdict(list)
        for event in self.store.list_events():
            by_sector[event.sector.value].append(event)

        for event in raw_events:
            event.witness.reputation = self.reputation_model.score(event.witness.source_id)
            self.store.source_reputation[event.witness.source_id] = event.witness.reputation

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
            if self.store.is_published(canonical.event_id):
                continue

            claims = extract_claims(canonical)
            draft = compose_post(claims)
            ok, _reason = judge_draft(draft, claims)
            if not ok:
                dropped += 1
                continue

            receipts = await self.fanout.publish(canonical.event_id, draft)
            if not self._has_successful_channel(receipts):
                dropped += 1
                continue

            self.store.mark_published(canonical.event_id)
            for witness in canonical.witnesses:
                new_score = self.reputation_model.mark_success(witness.source_id)
                self.store.source_reputation[witness.source_id] = new_score
            published += 1

        return {
            "raw": len(raw_events),
            "accepted": accepted,
            "published": published,
            "dropped": dropped,
        }

    def get_ingestor_stats(self) -> dict[str, dict[str, int | str | None]]:
        return self.ingestor_stats

    @staticmethod
    def _has_successful_channel(receipts: dict[str, str]) -> bool:
        for value in receipts.values():
            if value.startswith("error:"):
                continue
            if value.startswith("skipped:"):
                continue
            return True
        return False

    async def retract(self, event_id: str, reason: str) -> bool:
        event = self.store.get_event(event_id)
        if event is None:
            return False
        if self.store.is_retracted(event_id):
            return False
        for witness in event.witnesses:
            new_score = self.reputation_model.mark_retraction(witness.source_id)
            self.store.source_reputation[witness.source_id] = new_score
        triggered = self.circuit_breaker.record_retraction(event.sector)
        await self.fanout.publish_correction(event_id, reason)
        self.store.mark_retracted(event_id)
        return triggered
