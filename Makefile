.PHONY: install dev lint test run

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
