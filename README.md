# Shitposter

Autonomous breaking-news broadcaster for geopolitics, macro, and crypto. Ingests
multi-tier sources, clusters corroborating witnesses, composes short copy with
Claude under a strict hallucination-prevention loop, and fans out to Telegram
(primary), Bluesky, Mastodon, an RSS feed, and X (budgeted).

Design write-up lives in the approved plan file. See `src/pipeline/verify.py`
for the publish-gate, `src/llm/judge.py` for the hallucination guard, and
`src/publish/fanout.py` for the multi-platform fanout.

## Quickstart

```bash
cp .env.example .env
# fill in ANTHROPIC_API_KEY, TELEGRAM_*, X_*, BLUESKY_*
docker compose up -d postgres redis
docker compose run --rm app alembic upgrade head
docker compose run --rm app python -m scripts.seed_sources
docker compose up -d
```

Open `http://localhost:8000/stats`. Kill-switch: `POST /admin/pause`.

## Stages

```
INGEST -> DEDUPE+CLUSTER -> VERIFY -> COMPOSE+JUDGE -> PUBLISH
```

Each stage reads/writes a Redis Stream; state lives in Postgres.

## Verification plan

1. `python -m scripts.backtest events.jsonl` — precision/recall/latency.
2. `python -m scripts.shadow_run` — run live but block X writes.
3. Canary on X at 10 posts/mo for two weeks with nightly
   `python -m scripts.shadowban_probe <handle>`.
4. Promote to 40 posts/mo + 2 satellite accounts.
