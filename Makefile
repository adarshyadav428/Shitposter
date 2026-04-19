.PHONY: dev up down migrate seed logs test lint fmt shell

dev: ## Start infra (Postgres + Redis) for local development
	docker compose up -d postgres redis
	@echo "Postgres on :5432, Redis on :6379"

up: ## Start full stack (all services)
	docker compose up -d

down: ## Stop all services
	docker compose down

migrate: ## Run Alembic migrations
	docker compose run --rm app alembic upgrade head

seed: ## Seed the sources table
	docker compose run --rm app python -m scripts.seed_sources

logs: ## Tail app logs
	docker compose logs -f app

test: ## Run the test suite (requires local infra)
	pytest tests/ -v --tb=short

lint: ## Run ruff linter
	ruff check src/ tests/ scripts/

fmt: ## Auto-format with ruff
	ruff format src/ tests/ scripts/

shell: ## Open a Python REPL inside the app container
	docker compose run --rm app python

shadowban-probe: ## Check X shadowban status (usage: make shadowban-probe HANDLE=yourhandle)
	docker compose run --rm app python -m scripts.shadowban_probe $(HANDLE)

retraction-audit: ## Run the weekly retraction audit
	docker compose run --rm app python -m scripts.retraction_audit

cost-report: ## Print Anthropic API cost estimate
	docker compose run --rm app python -m scripts.cost_report

shadow-mode: ## Enable shadow mode (Telegram/Bluesky/Mastodon only, X blocked)
	docker compose run --rm app python -m scripts.shadow_run

pause: ## Trip the global kill switch
	curl -s -XPOST http://localhost:8000/admin/pause | python3 -m json.tool

resume: ## Lift the global kill switch
	curl -s -XPOST http://localhost:8000/admin/resume | python3 -m json.tool

stats: ## Print pipeline stats
	curl -s http://localhost:8000/stats | python3 -m json.tool

sources: ## Print source reputation table
	curl -s http://localhost:8000/admin/sources | python3 -m json.tool

circuit: ## Print circuit breaker status
	curl -s http://localhost:8000/admin/circuit | python3 -m json.tool

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
