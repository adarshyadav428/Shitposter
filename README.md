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

## Runtime Modes

- API mode: starts autonomous autopilot loop by default.
- Manual mode: call `/run-once` for deterministic single-cycle execution.
- CLI mode: `python -m newsbot.main` runs forever with configured poll interval.

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
- `GET /events.json`
- `GET /rss.xml`
- `POST /admin/pause`
- `POST /admin/resume`
- `POST /admin/retract/{event_id}`
- `GET /admin/sources`
- `GET /admin/circuit`
- `GET /admin/budget`
- `GET /admin/autopilot`
- `POST /admin/autopilot/start`
- `POST /admin/autopilot/stop`

## Source Fleet

- Mock sources are enabled by default for deterministic startup.
- Real RSS fleet can be enabled with `ENABLE_REAL_RSS=true`.
- Source toggles live in `.env`:
   - `USE_MOCK_INGESTORS`
   - `ENABLE_REAL_RSS`
   - `AUTOPILOT_ENABLED`
   - `POLL_INTERVAL_SECONDS`

## Durability

- Runtime state is snapshotted to disk by default.
- Configure with:
   - `ENABLE_STATE_SNAPSHOT`
   - `STATE_SNAPSHOT_PATH`

## Notes

- This codebase is designed to run with zero manual intervention once configured.
- Safety defaults are strict; uncertain events are dropped.
