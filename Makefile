# EntShifa monorepo commands (see README.md).
# Requires: Docker with Compose v2, Make (Git for Windows / WSL / macOS / Linux).

COMPOSE ?= docker compose
ENV_FILE ?= .env
API_DIR := apps/api
WEB_DIR := apps/web

.PHONY: dev dev-down dev-logs worker help
.PHONY: lint lint-api lint-web typecheck typecheck-api typecheck-web
.PHONY: test test-unit test-integration test-clinical test-cov import-check migrate-check
.PHONY: contracts contracts-check i18n-check anonymize build-web e2e security

help: ## Show available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  %-18s %s\n", $$1, $$2}'

dev: ## Start MySQL, Redis, and MinIO (creates .env from .env.example if missing)
	@if [ ! -f "$(ENV_FILE)" ]; then cp .env.example "$(ENV_FILE)"; fi
	$(COMPOSE) --env-file $(ENV_FILE) up -d --wait
	$(COMPOSE) --env-file $(ENV_FILE) --profile init run --rm minio-init

dev-down: ## Stop local infrastructure
	$(COMPOSE) --env-file $(ENV_FILE) down

dev-logs: ## Follow infrastructure logs
	$(COMPOSE) --env-file $(ENV_FILE) logs -f --tail=100

worker: ## Run the background job worker (requires Redis + migrated MySQL)
	cd $(API_DIR) && python -m ent.jobs.worker

lint: lint-api lint-web ## Run Python and TypeScript linters and format checks

lint-api: ## ruff, black (API)
	cd $(API_DIR) && python -m ruff check src tests
	cd $(API_DIR) && python -m ruff format --check src tests
	cd $(API_DIR) && python -m black --check src tests

lint-web: ## eslint and prettier (web)
	cd $(WEB_DIR) && npm run lint
	cd $(WEB_DIR) && npm run format:check

typecheck: typecheck-api typecheck-web ## mypy + tsc

typecheck-api: ## mypy strict on ent
	cd $(API_DIR) && python -m mypy --strict src

typecheck-web: ## TypeScript noEmit
	cd $(WEB_DIR) && npm run typecheck

import-check: ## Backend import boundary contracts (import-linter)
	cd $(API_DIR) && lint-imports
	cd $(API_DIR) && python scripts/check_router_imports.py

test-unit: ## Fast tests (no Docker)
	cd $(API_DIR) && python -m pytest -m "not integration and not clinical"

test-integration: ## Tests requiring MySQL, Redis, MinIO
	cd $(API_DIR) && python -m pytest -m integration

test-clinical: ## Known-answer clinical tests
	cd $(API_DIR) && python -m ent.cli.verify_engines

test-cov: ## Full suite with coverage thresholds
	cd $(API_DIR) && python -m pytest --cov=ent --cov-report=term-missing --cov-report=json
	cd $(API_DIR) && python scripts/check_coverage.py

test: test-unit ## Default: fast tests only (use test-cov in CI)

migrate: ## Apply Alembic migrations to head
	cd $(API_DIR) && python -m alembic upgrade head

migrate-down: ## Downgrade one Alembic revision
	cd $(API_DIR) && python -m alembic downgrade -1

migrate-check: ## Migrations on empty DB and incremental upgrade
	cd $(API_DIR) && python scripts/migration_check.py

seed: ## Load local dev identity/auth seed (demo users; run after migrate)
	cd $(API_DIR) && python -m ent.cli.seed

contracts: ## Export OpenAPI from FastAPI and generate TypeScript types
	cd $(API_DIR) && python -m ent.cli.export_openapi
	node packages/contracts/scripts/generate.mjs

contracts-check: ## Fail if committed OpenAPI/types disagree with the API
	node packages/contracts/scripts/check.mjs

i18n-check: ## Verify translation catalogs (key parity, placeholders, no orphans)
	node packages/i18n-messages/scripts/check.mjs

build-web: ## Next.js production build
	cd $(WEB_DIR) && npm run build

e2e: ## Playwright smoke (en / fr / ar)
	cd $(WEB_DIR) && npm run e2e

security: ## Dependency and secret scanning (API + web)
	cd $(API_DIR) && python -m pip_audit --ignore-vuln PYSEC-2026-2280 --ignore-vuln PYSEC-2026-2281
	cd $(WEB_DIR) && npm audit --audit-level=critical

anonymize: ## Build an anonymized development database dump (implemented in P1-11)
	@bash infra/scripts/anonymize.sh
