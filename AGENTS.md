# ENT Clinical Workspace: agent instructions

Read this before writing any code in this repository. These rules are not
suggestions. Code that violates them fails CI.

## What this project is

A clinical web application for ENT (otolaryngology) doctors. It stores
examinations, audiograms, endoscopy findings, questionnaires, prescriptions,
surgical records and reports as structured clinical data, and generates
documents from that data in multiple languages.

This is medical software. A wrong calculation, a leaked record across clinics,
or a silently mutated signed report is not a bug to fix next sprint. Correctness
and traceability outrank speed of delivery and cleverness.

Reference documents in `docs/`:
- `docs/clinical/feature-specification.txt` — what the product does, phase plan
- `docs/architecture/architecture-and-structure.txt` — layering, schema, conventions

When those documents and this file disagree, this file wins for code style and
the architecture document wins for design decisions. If a request contradicts
either, say so before writing the code.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2
- Frontend: Next.js (App Router), React, TypeScript strict, Tailwind, shadcn/ui
- Database: MySQL 8 (InnoDB, utf8mb4)
- Storage: S3-compatible object storage. Cache and queue: Redis
- Tests: pytest (backend), Vitest + React Testing Library + Playwright (frontend)

Do not introduce a new library, framework or service without being asked. If a
task seems to need one, propose it and wait.

## The ten rules

1. **Dependencies point inward.** Router to service, service to repository and
   domain. Nothing in `engines/` imports FastAPI, SQLAlchemy or anything doing
   I/O.
2. **One feature owns one domain.** Code is grouped by clinical domain
   (`patients`, `audiology`, `endoscopy`), never by technical type. There is no
   global `models.py` holding unrelated tables.
3. **Only repositories touch the database.** Services never write a query.
   Routers never see an ORM object.
4. **Clinical math is a pure function** in `engines/`, with a version, a cited
   reference and known-answer tests. It never runs in the browser.
5. **Everything crossing a boundary is typed.** Pydantic on the backend,
   generated TypeScript types on the frontend. No untyped dicts, no `any`.
6. **No user-visible string is hardcoded.** Not in JSX, not in an API response,
   not in an error message. UI strings are translation keys; clinical terms are
   database concepts.
7. **Reference data is data.** Formulary, questionnaires, protocols, templates,
   terminology live in versioned tables an admin edits. Not in code.
8. **Signed clinical records are immutable.** Corrections are addenda. Every
   read and write of a clinical record is audited.
9. **Every clinical value carries provenance:** who recorded it, when, from
   which source, and whether a human confirmed it.
10. **If it happens more than twice, extract a primitive.** Base repository,
    field components, query key factory, map engine. Write it once.

## Multi-tenancy: the rule that must never be broken

Every clinical table has `clinic_id`. Every query is scoped by it. This is
enforced in `BaseRepository`, not by remembering to add a `WHERE` clause.

- Never write a query against a clinical table that bypasses `_base_query()`.
- Never accept a `clinic_id` from the request body. It comes from the
  authenticated session.
- A cross-tenant read must return 404, never 403. A 403 confirms the record
  exists.

## Internationalization: non-negotiable from the first line

The app ships in English and French and will add Arabic (right to left) and
others. There are four kinds of text and each has its own mechanism.

| Kind | Example | Mechanism |
|---|---|---|
| UI chrome | button labels, validation messages | translation catalogs, keyed |
| Clinical terminology | findings, diagnoses, anatomy, drugs | `concept` + `concept_translation` rows |
| Generated narrative | report sentences built from findings | narrative engine, phrase templates per locale |
| User-authored text | doctor's conclusion, clinic footer | stored as written, tagged with its locale |

Rules:
- Never hardcode a display string anywhere, including in Python.
- Never store a clinical term as text. Store a `concept_id`.
- API errors return a stable `code` plus `context`. The frontend translates by
  code. The backend never sends a sentence meant to be displayed as is.
- Translation keys are semantic, never the English text:
  `audiology.audiogram.actions.addThreshold`, not `"Add threshold"`.
- Use ICU message format for plurals and interpolation. Arabic has six plural
  categories; string concatenation is banned.
- Units (dB HL, Hz, daPa, mg/kg, mL, mmHg) are never translated.

## Naming

**Python**: `snake_case` modules and functions, `PascalCase` classes,
`UPPER_SNAKE` constants. Schemas are `<Entity><Action>` (`AudiogramCreate`,
`AudiogramRead`). Services `<Domain>Service`. Repositories `<Entity>Repository`.
Errors `<Thing><Problem>Error`. Events are past tense (`AudiogramCreated`).

**TypeScript**: `PascalCase.tsx` for components, `useCamelCase.ts` for hooks,
`<domain>.<role>.ts` for feature files (`audiology.api.ts`). Props are
`<Component>Props`. Booleans start with `is`/`has`/`should`/`can`. Handlers are
`handleX` internally and `onX` as props.

**Database**: singular `snake_case` tables, `snake_case` columns, `*_at` for
datetimes, `*_date` for dates, `is_`/`has_` for booleans, `ix_`/`uq_`/`fk_`
index prefixes.

**API**: camelCase JSON on the wire, snake_case in Python. The base schema
converts; never do it by hand.

## Definition of done for any change

- Types check clean (`mypy --strict` on `src/`, `tsc --noEmit`).
- Lint clean (`ruff`, `eslint`), formatted (`black`, `prettier`).
- Tests written in the same change, not "later". New engine code has
  known-answer tests citing a source.
- Frontend: every interactive and test-asserted visible element exposes a
  `data-testid` via `apps/web/src/lib/test/test-id.ts` (no inline literals).
  Playwright selects by test id only, never by translated UI copy.
- No new translation key missing from any locale catalog.
- No hardcoded user-visible string.
- Tenant scoping verified for any new query.
- If the change touches a clinical calculation, the engine `VERSION` is bumped
  and the reference is recorded.

## How to work with me

- If the request is ambiguous about clinical behaviour, ask. Guessing at medical
  logic is worse than a delay.
- Do not invent clinical thresholds, scoring formulas, drug doses or staging
  tables from memory. Use the values in `docs/`, or ask, and mark anything
  uncertain with a `# VERIFY:` comment naming what needs checking.
- Work one ticket at a time. Do not scaffold future phases unprompted.
- When a file gets long (router over ~200 lines, service over ~400), split it
  along the lines described in the architecture document rather than continuing.
- Prefer editing an existing pattern over inventing a new one. The `patients`
  feature is the reference implementation; copy its shape.
- If you find yourself about to violate a rule here because it seems easier,
  stop and say so instead.

## Anti-patterns that will be rejected in review

- Clinical math in TypeScript
- Findings stored as free text or as a JSON blob
- Hardcoded user-visible strings
- Business logic in a router
- A query on a clinical table without `clinic_id`
- Mutating a signed encounter, report or operative note
- Deep cross-feature imports (`@/features/a/components/internal/b`)
- A wide examination table with dozens of nullable columns
- A list endpoint without pagination
- `SELECT *`, N+1 queries in timelines
- Floats for money or for exact measurements
- `ON DELETE CASCADE` on clinical tables
- Building AI features before the structured data layer is solid
- E2E or RTL tests that locate controls by visible text, placeholder, or
  translated `getByRole` name instead of `data-testid`
