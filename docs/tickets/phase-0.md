# Phase 0: skeleton and foundations

**Goal:** build the spine every later feature copies. Nothing clinical yet.
**Estimated:** 3 weeks.
**Reference:** architecture document sections 3 to 10 and section 40.

Do not start Phase 1 until every ticket here is done and reviewed. Rushing this
phase is the single most expensive mistake available on this project, because
30 feature modules will copy whatever shape you set here.

---

## - [x] P0-01 Monorepo and local environment

**Scope**
- Create the repo layout: `apps/api`, `apps/web`, `apps/worker`,
  `packages/contracts`, `packages/i18n-messages`, `packages/config`, `infra/`,
  `docs/`.
- `docker-compose.yml` with MySQL 8, Redis, MinIO, and healthchecks.
- `Makefile` with: `dev`, `test`, `lint`, `typecheck`, `migrate`, `seed`,
  `contracts`, `anonymize`.
- `.env.example` listing every variable with a comment and a safe dummy value.
- `README.md` with the setup steps a new developer follows.

**Acceptance**
- `make dev` brings up the full stack from a clean clone on a new machine.
- No secret is committed. `.env` is gitignored.

---

## - [x] P0-02 Settings and health endpoints

**Scope**
- `settings.py` using pydantic-settings. Every value from the environment.
- Fail fast at startup on a missing or invalid value, with a clear message.
- `/health/live` (process up) and `/health/ready` (MySQL, Redis, storage
  reachable).

**Acceptance**
- Removing a required env var stops startup with a readable error naming the
  variable, not a stack trace.

---

## - [x] P0-03 Database core

**Scope**
- `core/db/base.py`: declarative base with the index naming convention.
- `core/db/session.py`: async engine, session factory, `get_session` dependency.
- `core/db/mixins.py`: `PublicIdMixin` (ULID), `TimestampMixin`, `AuditMixin`,
  `SoftDeleteMixin`, `TenantMixin`, `VersionMixin`.
- `core/db/types.py`: `ULIDType` (CHAR(26), sortable), `EncryptedString`,
  `LateralityType`, `Quantity` composite.
- Alembic configured, first migration creating `clinic`, `site`, `user`,
  `role`, `permission`, `role_permission`, `user_clinic_role`, `user_session`.

**Acceptance**
- The first migration applies cleanly to an empty database and downgrades
  cleanly.
- Mixins produce exactly the columns listed in architecture section 23.
- ULIDs are lexicographically sortable and unique under concurrent insert.

**Reference:** architecture sections 23 and 25.1.

---

## - [x] P0-04 Security core

**Scope**
- `core/security/passwords.py`: argon2id hashing.
- `core/security/tokens.py`: access token (15 min, in memory), refresh token
  (HttpOnly Secure SameSite cookie) with rotation and reuse detection.
- `core/security/permissions.py`: the `Permission` enum and the role matrix.
- `core/security/dependencies.py`: `CurrentUser`, `require(Permission)`,
  active clinic resolution.
- Login, refresh, logout endpoints. Login throttling per account and per IP.

**Acceptance**
- A replayed refresh token revokes the whole session family.
- The active clinic comes from the session, never from a request body.
- A user with the wrong permission gets 403; a user from another clinic gets
  404.

**Reference:** architecture section 29.

---

## - [x] P0-05 Errors, context and audit

**Scope**
- `core/errors/`: the `DomainError` hierarchy, the error code enum, FastAPI
  handlers producing RFC 7807 problem+json with `code`, `context`, `requestId`.
- `core/context.py`: contextvars for request id, user, clinic.
- `core/audit/`: request context middleware and the audit recorder writing
  `audit_log` and `access_log`.

**Acceptance**
- Every error response has a stable namespaced code and no English sentence
  intended for display.
- Every write to a clinical table produces an audit row with before and after
  images and the changed field list.
- An unhandled exception returns a generic code and logs the full trace with
  the request id.

**Reference:** architecture sections 30 and 31.

---

## - [x] P0-06 Repository and schema base

**Scope**
- `core/repository/base.py`: `BaseRepository[Model]` with tenant and
  soft-delete filtering applied in `_base_query()`.
- `core/repository/filters.py`: the declarative filter builder.
- `core/repository/pagination.py`: cursor and offset pagination, with a
  maximum page size enforced.
- `core/schemas/base.py`: `CamelModel`, `ORMModel`, `PageSchema`.
- `core/schemas/common.py`: `CodeableConcept`, `Quantity`, `Laterality`,
  `Period`, `Attachment`, `Provenance`.
- `core/db/unit_of_work.py`: transaction boundary, events flushed after commit.

**Acceptance**
- A repository method cannot return rows from another clinic, proven by test.
- A list call without pagination parameters still returns a bounded page.
- JSON output is camelCase while Python stays snake_case, with no manual
  conversion anywhere.

**Reference:** architecture sections 7.1 to 7.3.

---

## - [x] P0-07 Event bus and worker

**Scope**
- `core/events/bus.py`: in-process pub/sub, subscribe and publish.
- `jobs/worker.py` and `jobs/scheduler.py` with one real job end to end.
- `jobs/base.py`: retry with backoff, idempotency keys, dead-letter recording
  in `job_run`.

**Acceptance**
- Events publish only after the transaction commits.
- Re-running a job with the same idempotency key does not duplicate its effect.

**Reference:** architecture sections 7.5 and 9.

---

## - [x] P0-08 Terminology module

**Scope**
- Models: `code_system`, `concept`, `concept_translation`,
  `concept_relationship`, `value_set`, `value_set_member`.
- Repository with locale-aware resolution: clinic override in requested locale,
  then global in requested locale, then clinic default locale, then code with a
  missing-translation marker.
- Endpoints: concept search (fulltext, accent-insensitive), value set fetch,
  concept dictionary bulk fetch for frontend caching.
- Seed script with the first anatomy concepts and a small findings value set.

**Acceptance**
- The same concept renders correctly in en and fr without a code change.
- Searching for an accented French term works with and without accents.
- Adding a locale requires only new translation rows.

**Reference:** architecture sections 20 and 25.2. This ticket unblocks
everything clinical, so do not shortcut it.

---

## - [x] P0-09 Frontend skeleton

**Scope**
- Next.js App Router with the `[locale]` segment and `middleware.ts` for locale
  negotiation and auth redirect.
- Tailwind, shadcn/ui installed, design tokens in `styles/tokens.css`.
- `providers/`: query, theme, locale, session, permission, toast.
- `lib/api/client.ts`, `lib/api/query-keys.ts`, `lib/api/errors.ts`.
- `lib/test/test-id.ts`: `testId`, `testIdProps`, and a `testIds` registry;
  dynamic helpers for ids that include public ids.
- `components/layout/`: AppShell, Sidebar, Topbar, PageHeader.
- Login flow end to end against P0-04.
- `data-testid` on login, shell, and error surfaces via the test-id factory only.

**Acceptance**
- Login works, session persists, logout clears it.
- An API error renders a translated message resolved from its code.
- No hardcoded user-visible string exists in the codebase.
- Playwright (or RTL smoke for login) finds controls by `data-testid` only, not
  by English or French copy.

---

## - [x] P0-10 Shared UI systems

**Scope**
- `components/data/DataTable` with server-side sorting and pagination,
  URL-synced filters, column visibility, loading, empty and error states.
- `components/forms/`: Form wrapper, `TextField`, `NumberField`, `SelectField`,
  `DateField`, `LateralityField`, `ConceptField`, `ScaleField`,
  `AutosaveIndicator`, `DirtyGuard`.
- `lib/forms/createForm.ts` and `lib/forms/autosave.ts`.

**Acceptance**
- A new list screen is built by defining columns only.
- A new form field renders label, description, error, required marker, unit and
  RTL correctly with no per-feature CSS.
- Server field errors map back onto the matching inputs automatically.
- Shared field and table components apply `data-testid` from field/column ids
  through `lib/test/test-id.ts` without per-feature duplication.

**Reference:** architecture sections 13.3 to 13.5.

---

## - [x] P0-11 Internationalization end to end

**Scope**
- next-intl configured under `apps/web/src/lib/i18n/` (architecture §11).
- Catalogs in `packages/i18n-messages` for `en`, `fr`, and placeholder `ar`.
- `lib/i18n/format.ts` for dates, numbers, units and names.
- CI check: every key present in every locale, no orphan keys, matching
  placeholder sets (`make i18n-check`).

**Acceptance**
- Switching locale changes the whole UI with no page rebuild.
- Setting `dir="rtl"` produces a correct layout with no mirrored stylesheet.
- Locale switcher offers only real languages (`en`, `fr`, `ar`).

**Reference:** architecture sections 18, 19 and 22.

---

## - [x] P0-12 Contracts pipeline

**Scope**
- Generate OpenAPI from FastAPI into `packages/contracts`.
- Generate TypeScript types from that spec.
- `make contracts` runs both. CI fails if the committed spec and the code
  disagree.

**Acceptance**
- Renaming a backend field breaks the frontend build, not production.

---

## - [x] P0-13 Storage and attachments core

**Scope**
- `integrations/storage/`: the port plus S3/MinIO and local adapters.
- Pre-signed upload and download URLs. Key layout
  `clinic/{clinicId}/patient/{patientPublicId}/{category}/{ulid}.{ext}`.
- Worker job: EXIF strip, malware scan hook, thumbnail and preview variants,
  checksum.
- `attachment` and `media_variant` models plus a viewer component.

**Acceptance**
- Large files never pass through the API process.
- Download URLs are short-lived, permission-checked and logged.
- EXIF location data is removed from every uploaded clinical photo.

**Reference:** architecture section 34.

---

## - [x] P0-14 CI pipeline

**Scope**
All twelve gates from architecture section 37: lint, format, type check, import
boundaries, unit tests, clinical known-answer tests, integration tests, API
contract check, translation check, migration check, frontend build, e2e,
security scan.

**Acceptance**
- A pull request violating a layering rule fails on the import boundary check,
  not in review.
- A missing translation key fails the build.
- Coverage thresholds enforced: 100% on `engines/`, 85% on services.
