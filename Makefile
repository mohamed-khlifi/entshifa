# EntShifa monorepo commands (see README.md).
# Requires: Docker with Compose v2, Make (Git for Windows / WSL / macOS / Linux).

COMPOSE ?= docker compose
ENV_FILE ?= .env

.PHONY: dev dev-down dev-logs test lint typecheck migrate seed contracts anonymize help

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

test: ## Run backend and frontend tests (implemented in later P0 tickets)
	@echo "test: not implemented until P0-03 (API) and P0-09 (web)."
	@exit 1

lint: ## Run linters (implemented in P0-14)
	@echo "lint: not implemented until P0-14."
	@exit 1

typecheck: ## Run mypy and tsc (implemented in P0-03 / P0-09)
	@echo "typecheck: not implemented until P0-03 (API) and P0-09 (web)."
	@exit 1

migrate: ## Apply database migrations (implemented in P0-03)
	@echo "migrate: not implemented until P0-03 (Alembic)."
	@exit 1

seed: ## Load system and demo reference data (implemented in P0-08)
	@echo "seed: not implemented until P0-08."
	@exit 1

contracts: ## Regenerate OpenAPI spec and TypeScript types (implemented in P0-12)
	@echo "contracts: not implemented until P0-12."
	@exit 1

anonymize: ## Build an anonymized development database dump (implemented in P1-11)
	@bash infra/scripts/anonymize.sh
