SHELL := /bin/zsh

.PHONY: help bootstrap api-test api-test-e2e api-test-integration api-test-unit web-test test lint api-lint web-lint typecheck api-typecheck web-typecheck no-any coverage api-coverage web-coverage worker-coverage coverage-all web-browser-contract app-authz-integration sqlite-compat perf check dev-api clean

help:
	@echo "Targets:"
	@echo "  make bootstrap  - sync Python deps with uv and install pnpm workspace deps"
	@echo "  make test       - run API and web tests"
	@echo "  make lint       - run API and web lint checks"
	@echo "  make typecheck  - run Python and TypeScript type checks"
	@echo "  make no-any     - fail if Python source contains explicit Any"
	@echo "  make coverage   - run API tests with coverage threshold (>= 90%)"
	@echo "  make coverage-all - run API, web, and worker coverage gates (>= 90% each)"
	@echo "  make web-browser-contract - run Playwright browser route contract checks"
	@echo "  make app-authz-integration - run cross-workspace app authorization checks"
	@echo "  make sqlite-compat - run SQLite secure/vector compatibility checks"
	@echo "  make perf       - run API and memory performance benchmarks"
	@echo "  make check      - run lint, typecheck, no-any, and coverage-all gates"
	@echo "  make dev-api    - run FastAPI dev server"
	@echo "  make clean      - remove local caches"

bootstrap:
	UV_PROJECT_ENVIRONMENT=.venv uv sync --all-groups
	pnpm install

api-test:
	PYTHONPATH=. uv run python -m unittest discover -s apps/api/tests -t .

api-test-e2e:
	PYTHONPATH=. uv run python -m unittest discover -s apps/api/tests/e2e -t .

api-test-integration:
	PYTHONPATH=. uv run python -m unittest discover -s apps/api/tests/integration -t .

api-test-unit:
	PYTHONPATH=. uv run python -m unittest discover -s apps/api/tests/unit -t .

web-test:
	pnpm --filter elara-web test

test: api-test web-test

api-lint:
	uv run ruff check apps/api

web-lint:
	pnpm --filter elara-web lint

lint: api-lint web-lint

api-typecheck:
	PYTHONPATH=. uv run mypy

web-typecheck:
	pnpm --filter elara-web typecheck

typecheck: api-typecheck web-typecheck

no-any:
	@! rg -n "\\bAny\\b" apps/api apps/worker --glob '*.py'

api-coverage:
	PYTHONPATH=. uv run coverage run --data-file=.coverage.api --source=apps/api -m unittest discover -s apps/api/tests -t .
	uv run coverage report --data-file=.coverage.api --fail-under=90

web-coverage:
	pnpm --filter elara-web coverage

worker-coverage:
	PYTHONPATH=. uv run coverage run --data-file=.coverage.worker --source=apps/worker -m unittest discover -s apps/worker/tests -t .
	uv run coverage report --data-file=.coverage.worker --fail-under=90

coverage-all: api-coverage web-coverage worker-coverage

coverage: api-coverage

web-browser-contract:
	pnpm --filter elara-web test:browser-contract

app-authz-integration:
	PYTHONPATH=. uv run python -m unittest apps.api.tests.integration.test_app_authz_integration

sqlite-compat:
	PYTHONPATH=. uv run python scripts/compat/check_sqlite_vector_compat.py

perf:
	PYTHONPATH=. uv run python scripts/perf/fixtures/generate_fixture_dataset.py
	PYTHONPATH=. uv run python scripts/perf/run_api_latency.py
	PYTHONPATH=. uv run python scripts/perf/run_memory_retrieval.py

dev-api:
	PYTHONPATH=. uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

check: lint typecheck no-any coverage-all

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -type f -delete
	rm -rf .ruff_cache .pytest_cache .mypy_cache .coverage .coverage.api .coverage.worker .venv
