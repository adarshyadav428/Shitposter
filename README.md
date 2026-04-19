# Autonomous News Broadcaster

This repository implements a production-oriented autonomous breaking-news system with hard verification gates and anti-platform-suppression controls.

## What It Solves

- Latency vs verification: tiered publish gates by source quality and independent witness count.
- Hallucination risk: composition must pass deterministic claim checks.
- X survivability: budget caps, cadence jitter, warmup gate, and kill switch.

## Core Pipeline

1. Ingest from high-trust and medium-trust sources.
2. Dedupe and cluster by entity overlap and simhash distance.
3. Verify with hard gates:
   - one Tier 1 source can publish immediately
   - two independent Tier 2 sources can publish
   - one Tier 2 source alone is held and expires
   - Tier 3 alone never publishes
4. Compose + judge from extracted claims only.
5. Fanout to Telegram, Bluesky, Mastodon, RSS, X (optional).

## Run Locally

1. Copy `.env.example` to `.env` and set required secrets.
2. Install deps:
   - `pip install -e .[dev]`
3. Start API:
   - `uvicorn newsbot.api:app --reload`

## API

- `GET /health`
- `GET /stats`
- `GET /events`
- `POST /admin/pause`
- `POST /admin/resume`
- `POST /admin/retract/{event_id}`
- `GET /admin/sources`
- `GET /admin/circuit`
- `GET /admin/budget`

## Notes

- This codebase is designed to run with zero manual intervention once configured.
- Safety defaults are strict; uncertain events are dropped.
