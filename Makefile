.PHONY: install dev lint test run docker-build docker-up docker-down docker-up-prod smoke predeploy predeploy-prod

install:
	pip install -e .[dev]

dev:
	uvicorn newsbot.api:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check src tests

test:
	pytest -q

run:
	python -m newsbot.main

docker-build:
	docker build -t autonomous-news-broadcaster:local .

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-up-prod:
	docker compose -f docker-compose.prod.yml up -d

smoke:
	curl -fsS http://127.0.0.1:8000/health/live
	curl -fsS http://127.0.0.1:8000/health/ready

predeploy:
	python scripts/predeploy_check.py

predeploy-prod:
	python scripts/predeploy_check.py --env-file .env.production.example
