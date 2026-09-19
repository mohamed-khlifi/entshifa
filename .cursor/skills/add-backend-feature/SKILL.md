---
name: add-backend-feature
description: Scaffold a new backend feature module (router, service, repository, models, schemas, tests) following the project's layering. Use when adding any new clinical domain to the FastAPI app, such as vestibular, allergy, sleep, surgery or head and neck.
---

# Add a backend feature module

Every feature has the same shape. Copy `features/patients/` and replace the
clinical content. Do not invent a different structure.

## Before writing code

1. Confirm the domain name (singular, snake_case: `vestibular`, `allergy`).
2. Read the matching section of `docs/clinical/feature-specification.txt` so the
   fields match the clinical spec, not your assumption.
3. Confirm which tables this feature owns and whether any finding belongs in
   `observation` rather than a dedicated column (see `.cursor/rules/database.mdc`).
4. State the plan and the endpoint list before generating files.

## Steps

### 1. Models
`features/<domain>/models.py`. Inherit the mixins. Add the CHECK constraints and
indexes in the model, not only in the migration. Every clinical table gets
`clinic_id` and a `(clinic_id, patient_id, <date> DESC)` index.

### 2. Migration
Generate with Alembic, then review by hand. Add index names, CHECK constraints
and column comments autogenerate misses. Additive first.

### 3. Schemas
`schemas/requests.py`, `schemas/responses.py`. Inherit `CamelModel`. Separate
Create / Update / Read. Validate clinical ranges (frequency, threshold, score,
dose). Reuse `CodeableConcept`, `Quantity`, `Laterality`, `Provenance` from
`core.schemas.common`.

### 4. Repository
Subclass `BaseRepository[Model]`. Never bypass `_base_query()`. Declare eager
loading. Every list method paginates. No business rules.

### 5. Engines (if the feature computes anything)
Put the calculation in `engines/<domain>/`, not in the service. Use the
`add-clinical-calculator` skill.

### 6. Service
One public method per use case. Wrap writes in the unit of work. Call engines
for computed values. Emit domain events. Raise domain errors. Return schemas.

### 7. Policies
If access rules differ from the default (own patients / clinic patients),
put them in `policies.py` and call from the service.

### 8. Events and handlers
Declare events in `events.py` (past tense). If this feature must react to
another's events, subscribe in `handlers.py`. Never import another feature's
service directly for a side effect.

### 9. Router
Thin. `response_model` on every endpoint. Public ULID in paths. Permission
dependency per endpoint. State transitions as verb sub-resources.

### 10. Register
Mount the router in `main.py`, register handlers in the event bus wiring, add
permissions to the permission seed, add the feature to the role matrix seed.

### 11. Tests
- `tests/integration/test_<domain>_service.py`: the use cases
- `tests/api/test_<domain>_router.py`: status codes, permissions, pagination
- a cross-tenant isolation test (a user from clinic A gets 404, not 403)
- a factory in `tests/factories/`

### 12. Contracts
Run `make contracts` so the OpenAPI spec and the generated TypeScript types
update in the same change.

## Checklist before you say it is done

- [ ] No query bypasses `_base_query()`
- [ ] Router contains no business logic and no ORM object
- [ ] Every computed clinical value comes from an engine, with a version
- [ ] Every list endpoint paginates
- [ ] Cross-tenant test exists and passes
- [ ] No hardcoded user-visible string; errors use namespaced codes
- [ ] Permissions seeded, router mounted, contracts regenerated
