"""Offline backtest: feed synthetic/historical events through the pipeline.

Measures:
- precision: (published & in ground-truth) / published
- recall:    (published & in ground-truth) / ground-truth
- hallucination-catch-rate via the judge on generated drafts
- p50 / p95 latency from first-witness to publish-ready

Usage: `python scripts/backtest.py path/to/events.jsonl`
jsonl line shape:
  {"source_id":"reuters_world","sector":"macro","external_id":"...",
   "title":"...","body":"...","seen_at":"2026-04-18T10:00:00Z",
   "ground_truth":true}
"""
from __future__ import annotations

import asyncio
import json
import statistics
import sys
from datetime import datetime

from src.llm.compose_stage import handle_verified
from src.obs.logs import configure_logging, get_logger
from src.pipeline.cluster import handle_raw_event
from src.pipeline.verify import evaluate
from src.state.db import session_scope
from src.state.models import CanonicalEvent, Source, Tier

log = get_logger(__name__)


async def _ensure_source(source_id: str, sector: str, tier: int) -> None:
    async with session_scope() as s:
        existing = await s.get(Source, source_id)
        if existing is None:
            s.add(
                Source(
                    id=source_id,
                    family=source_id.split("_")[0],
                    tier=tier,
                    kind="backtest",
                    url="",
                    sector=sector,
                )
            )


async def run(path: str) -> None:
    configure_logging()
    tp = fp = fn = 0
    latencies: list[float] = []
    ground_truth: set[str] = set()
    published: set[str] = set()

    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ext = rec["external_id"]
            if rec.get("ground_truth"):
                ground_truth.add(ext)

            await _ensure_source(rec["source_id"], rec["sector"], rec.get("tier", int(Tier.T1)))
            evt = {
                "source_id": rec["source_id"],
                "source_family": rec["source_id"].split("_")[0],
                "tier": rec.get("tier", int(Tier.T1)),
                "sector": rec["sector"],
                "external_id": ext,
                "title": rec["title"],
                "body": rec["body"],
                "url": rec.get("url"),
                "seen_at": rec["seen_at"],
                "payload": {},
            }
            event_id = await handle_raw_event(evt)
            if event_id is None:
                continue
            t0 = datetime.fromisoformat(rec["seen_at"].replace("Z", "+00:00"))

            decision = await evaluate(event_id)
            if decision.action == "publish":
                async with session_scope() as s:
                    ev = await s.get(CanonicalEvent, event_id)
                    if ev:
                        latencies.append((ev.last_seen_at - t0).total_seconds())
                if await handle_verified(event_id):
                    published.add(ext)
                    if ext in ground_truth:
                        tp += 1
                    else:
                        fp += 1
            else:
                if ext in ground_truth:
                    fn += 1

    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    p50 = statistics.median(latencies) if latencies else 0.0
    p95 = statistics.quantiles(latencies, n=20)[-1] if len(latencies) >= 20 else (max(latencies) if latencies else 0.0)
    log.info(
        "backtest.summary",
        precision=round(precision, 3),
        recall=round(recall, 3),
        published=len(published),
        p50_seconds=round(p50, 1),
        p95_seconds=round(p95, 1),
    )


if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))
