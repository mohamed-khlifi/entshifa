# EntShifa monorepo commands (see README.md).
# Requires: Docker with Compose v2, Make (Git for Windows / WSL / macOS / Linux).

COMPOSE ?= docker compose
ENV_FILE ?= .env

.PHONY: dev dev-down dev-logs worker test lint typecheck migrate migrate-down seed contracts anonymize i18n-check help

help: ## Show available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  %-14s %s\n", $$1, $$2}'

dev: ## Start MySQL, Redis, and MinIO (creates .env from .env.example if missing)
	@if [ ! -f "$(ENV_FILE)" ]; then cp .env.example "$(ENV_FILE)"; fi
	$(COMPOSE) --env-file $(ENV_FILE) up -d --wait
	$(COMPOSE) --env-file $(ENV_FILE) --profile init run --rm minio-init

dev-down: ## Stop local infrastructure
	$(COMPOSE) --env-file $(ENV_FILE) down

dev-logs: ## Follow infrastructure logs
	$(COMPOSE) --env-file $(ENV_FILE) logs -f --tail=100

worker: ## Run the background job worker (requires Redis + migrated MySQL)
	cd apps/api && python -m ent.jobs.worker

test: ## Run backend unit tests (frontend tests land in P0-09)
	cd apps/api && python -m pytest -m "not integration"

lint: ## Run linters (implemented in P0-14)
	@echo "lint: not implemented until P0-14."
	@exit 1

typecheck: ## Run mypy on the API (tsc lands in P0-09)
	cd apps/api && python -m mypy --strict src

migrate: ## Apply Alembic migrations to head
	cd apps/api && python -m alembic upgrade head

migrate-down: ## Downgrade one Alembic revision
	cd apps/api && python -m alembic downgrade -1

seed: ## Load local dev identity/auth seed (demo users; run after migrate)
	cd apps/api && python -m ent.cli.seed

contracts: ## Regenerate OpenAPI spec and TypeScript types (implemented in P0-12)
	@echo "contracts: not implemented until P0-12."
	@exit 1

i18n-check: ## Verify translation catalogs (key parity, placeholders, no orphans)
	node packages/i18n-messages/scripts/check.mjs

anonymize: ## Build an anonymized development database dump (implemented in P1-11)
	@bash infra/scripts/anonymize.sh
