SHELL := /bin/zsh

.PHONY: help bootstrap api-test web-test test lint api-lint dev-api clean

help:
	@echo "Targets:"
	@echo "  make bootstrap  - sync Python deps with uv and install pnpm workspace deps"
	@echo "  make test       - run API and web tests"
	@echo "  make lint       - run API lint checks"
	@echo "  make dev-api    - run FastAPI dev server"
	@echo "  make clean      - remove local caches"

bootstrap:
	UV_PROJECT_ENVIRONMENT=.venv uv sync --all-groups
	pnpm install

api-test:
	PYTHONPATH=. uv run python -m unittest discover -s apps/api/tests -t .

web-test:
	pnpm --filter elara-web test

test: api-test web-test

api-lint:
	uv run ruff check apps/api

lint: api-lint

dev-api:
	PYTHONPATH=. uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -type f -delete
	rm -rf .ruff_cache .pytest_cache .venv
