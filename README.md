# EntShifa

Clinical web application for ENT (otolaryngology) practices. Monorepo layout and
local infrastructure are defined in `docs/architecture/architecture-and-structure.txt`.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Compose v2)
- [Make](https://www.gnu.org/software/make/) (included with Git for Windows, or use WSL)
- Python 3.12 and Node.js 20+ (required from **P0-03** / **P0-09** onward; not needed for P0-01 alone)

## Quick start (local infrastructure)

From the repository root (Unix shell or Git Bash):

```bash
cp .env.example .env
make dev
```

On **PowerShell** without `make`:

```powershell
Copy-Item .env.example .env
docker compose --env-file .env up -d --wait
docker compose --env-file .env --profile init run --rm minio-init
```

The `minio-init` job uses profile `init` so `up --wait` only waits on long-running
services (MySQL, Redis, MinIO). Bucket creation runs once via `mc` after MinIO is healthy.

This starts **MySQL 8**, **Redis**, and **MinIO** with health checks and creates the
configured S3 bucket. MinIO images are pulled from **Quay** (`quay.io/minio/*`) with
pinned release tags because `minio/minio` and `minio/mc` are no longer published on
Docker Hub. Application services (`apps/api`, `apps/web`, `apps/worker`) are added in
later Phase 0 tickets.

Verify services:

```bash
docker compose ps
```

| Service | Purpose | Local URL |
|---------|---------|-----------|
| MySQL | Primary database | `localhost:3306` |
| Redis | Cache and job queue | `localhost:6379` |
| MinIO | S3-compatible object storage | API `http://localhost:9000`, console `http://localhost:9001` |

Stop the stack:

```bash
make dev-down
```

## Repository layout

```
apps/
  api/          FastAPI backend (Python)
  web/          Next.js frontend (TypeScript)
  worker/       Background jobs (shares API code)
packages/
  contracts/    OpenAPI spec and generated TypeScript types
  i18n-messages/ UI translation catalogs
  config/       Shared ESLint, Prettier, and TypeScript presets
infra/
  docker/       Dockerfiles for deployable apps
  scripts/      backup, seed, anonymize helpers
docs/           Architecture, clinical spec, tickets, database DDL
```

## Make targets

| Command | Description |
|---------|-------------|
| `make dev` | Start local infrastructure |
| `make dev-down` | Stop infrastructure |
| `make test` | Fast unit tests (no Docker) |
| `make test-cov` | Full suite + coverage thresholds |
| `make test-integration` | Tests requiring MySQL/Redis |
| `make lint` | Linters (ruff, black, eslint, prettier) |
| `make import-check` | Backend import boundaries |
| `make typecheck` | mypy + `tsc` |
| `make migrate-check` | Alembic empty DB + incremental upgrade |
| `make build-web` | Next.js production build |
| `make e2e` | Playwright smoke (en / fr / ar) |
| `make security` | pip-audit + npm audit |
| `make migrate` | Alembic migrations (P0-03) |
| `make migrate-down` | Downgrade one Alembic revision |
| `make seed` | Reference data seeds (P0-08) |
| `make i18n-check` | Translation catalog parity (P0-11) |
| `make contracts` | Export OpenAPI + generate TypeScript types (P0-12) |
| `make contracts-check` | Fail if committed contracts disagree with the API |
| `make anonymize` | Anonymized dump script stub (full job in P1-11) |

Run `make help` for a short list.

## Secrets

Never commit `.env`. Only `.env.example` belongs in git. Use strong values outside
local development.

## Documentation

- Agent and code rules: `AGENTS.md`
- Architecture: `docs/architecture/architecture-and-structure.txt`
- Clinical product spec: `docs/clinical/feature-specification.txt`
- Work tickets: `docs/tickets/`

## Phase 0 status

Phase 0 (**P0-01**–**P0-14**) is complete when every ticket in
`docs/tickets/phase-0.md` is checked and CI is green on `main`. Do not start
Phase 1 until that review gate passes.
