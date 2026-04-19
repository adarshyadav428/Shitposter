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
- Optional admin auth: set `ADMIN_API_TOKEN` to protect all `/admin/*` endpoints.
   - Use header `X-Admin-Token: <token>` or `Authorization: Bearer <token>`.

## Run Locally

1. Copy `.env.example` to `.env` and set required secrets.
2. Install deps:
   - `pip install -e .[dev]`
3. Start API:
   - `uvicorn newsbot.api:app --reload`

## Deployment

- Production env template: `.env.production.example`
- Deployment runbook: `DEPLOYMENT.md`
- Release image workflow: `.github/workflows/release-image.yml`
- Self-hosted deploy workflow: `.github/workflows/deploy-self-hosted.yml`
- Production compose stack: `docker-compose.prod.yml`
- Config preflight checker: `make predeploy`
- Startup preflight gate: `ENFORCE_STARTUP_PREFLIGHT=true` (recommended)

## API

- `GET /health`
- `GET /health/live`
- `GET /health/ready`
- `GET /metrics`
- `POST /run-once`
- `GET /stats`
- `GET /events`
- `GET /events/{event_id}`
- `GET /events.json`
- `GET /rss.xml`
- `GET /dashboard`
- `GET /system/readiness`
- `GET /system/preflight`
- `GET /admin/publications`
- `GET /admin/publication-failures`
- `GET /admin/drops`
- `POST /admin/pause`
- `POST /admin/resume`
- `POST /admin/retract/{event_id}`
- `GET /admin/sources`
- `GET /admin/ingestors`
- `GET /admin/circuit`
- `GET /admin/budget`
- `GET /admin/retention`
- `POST /admin/prune`
- `POST /admin/state/save`
- `GET /admin/autopilot`
- `POST /admin/autopilot/start`
- `POST /admin/autopilot/stop`
- `GET /admin/retraction-monitor`
- `POST /admin/retraction-monitor/start`
- `POST /admin/retraction-monitor/stop`
- `POST /admin/retraction-monitor/scan`
- `GET /admin/heartbeat`
- `POST /admin/heartbeat/start`
- `POST /admin/heartbeat/stop`
- `POST /admin/heartbeat/send`

## Source Fleet

- Mock sources are enabled by default for deterministic startup.
- Real RSS fleet can be enabled with `ENABLE_REAL_RSS=true`.
- Source toggles live in `.env`:
   - `USE_MOCK_INGESTORS`
   - `ENABLE_REAL_RSS`
   - `AUTOPILOT_ENABLED`
   - `POLL_INTERVAL_SECONDS`

## Publishers

- Telegram, Bluesky, and Mastodon publishers are implemented.
- If credentials are missing, channels fall back to safe no-op publishing.
- Configure with:
   - `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   - `BLUESKY_IDENTIFIER`, `BLUESKY_APP_PASSWORD`
   - `MASTODON_BASE_URL`, `MASTODON_ACCESS_TOKEN`

## Durability

- Runtime state is snapshotted to disk by default.
- Configure with:
   - `ENABLE_STATE_SNAPSHOT`
   - `STATE_BACKEND` (`json` or `sqlite`)
   - `STATE_SNAPSHOT_PATH`
   - `STATE_SQLITE_PATH`
   - `RETENTION_ENABLED`
   - `RETENTION_MAX_EVENTS`
   - `RETENTION_MAX_PUBLICATIONS`
   - `RETENTION_MAX_FAILED_PUBLICATIONS`
   - `RETENTION_MAX_DROP_SAMPLES`
- When `STATE_BACKEND=sqlite` and the SQLite file is empty, the service will import
   existing JSON snapshot data once (if present) to ease backend migration.

## Retraction Monitoring

- Background monitor periodically rescans source URLs.
- If content changes and contains correction-like keywords, it auto-publishes a correction.
- Configure with:
   - `RETRACTION_MONITOR_ENABLED`
   - `RETRACTION_MONITOR_INTERVAL_SECONDS`

## Heartbeat

- Optional background heartbeat sends periodic liveness messages.
- Configure with:
   - `HEARTBEAT_ENABLED`
   - `HEARTBEAT_INTERVAL_SECONDS`

## Notes

- This codebase is designed to run with zero manual intervention once configured.
- Safety defaults are strict; uncertain events are dropped.
- RSS polling and outbound publisher calls use retry with exponential backoff.
