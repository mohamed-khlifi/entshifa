---
name: add-frontend-feature
description: Scaffold a new frontend feature folder (api, hooks, components, schemas, types) and its routes in the Next.js app. Use when adding the UI for a clinical domain, a new screen, or a new list/detail/form flow.
---

# Add a frontend feature

Mirror the backend feature name. Copy the shape of `features/patients/`.

## Before writing code

1. Confirm the backend endpoints exist and the generated types are current
   (`make contracts`).
2. Decide which parts are Server Components (read-only first paint) and which
   must be Client Components (interactivity).
3. List the translation keys you will need, and in which catalog file.
4. List the `testIds` you will need (or extend `lib/test/test-id.ts`) for every
   interactive and asserted visible element—locale-independent, no copy-based
   selectors.

## Steps

### 1. API layer
`features/<domain>/api/<domain>.api.ts` using `apiFetch` and the generated
request/response types. No hand-written response types.
`features/<domain>/api/<domain>.keys.ts` or an entry in the central query key
factory. Never inline a key literal.

### 2. Hooks
`useX` for queries, `useCreateX` / `useUpdateX` for mutations. Mutations
invalidate precise keys, roll back on error, and toast a translated message.
Set a sensible `staleTime`: reference data 1 hour, patient record 30 seconds,
terminology 24 hours.

### 3. Schemas
`schemas/<entity>.schema.ts` with zod. Validation messages are translation
keys. Mirror the backend validation; do not relax it.

### 4. Components
Build from `components/ui/`, `components/forms/`, `components/data/` and
`components/clinical/`. Do not restyle shadcn primitives per feature.
Match the light, modern clinical look defined in `.cursor/rules/frontend.mdc`
(tokens, Card, spacing, professional tone). Lists use `DataTable` from
`components/data`. Forms use `createClinicalForm` / `useClinicalForm` and the
shared field components in `components/forms`.
Wire `data-testid` through `testId` / `testIdProps` from `lib/test/test-id.ts`
(field `name`, table column id, or feature registry). Never hardcode test id
strings in JSX.

### 5. Routes
Add pages under `src/app/[locale]/(app)/...`. Pages compose and load; they
contain no business logic. Over ~80 lines means logic belongs in the feature.

### 6. Translations
Add `messages/<locale>/<domain>.json` for every locale in the same change.
Semantic keys, ICU plurals, no literals in JSX.

### 7. Barrel
Export the public surface from `features/<domain>/index.ts`. Other features
import only from there.

### 8. Tests
Component tests for any clinical input behaviour. Extend the Playwright flow if
this feature is part of a killer workflow. E2E steps use `getByTestId` only,
never translated labels or button text.

## Checklist

- [ ] No clinical arithmetic anywhere in this feature
- [ ] No hardcoded user-visible string
- [ ] No hand-written API types; all from `lib/api/generated`
- [ ] Query keys from the factory; mutations invalidate precisely
- [ ] Loading, empty and error states exist for every list
- [ ] Keyboard operable, labels tied to inputs, focus visible
- [ ] Translation keys added to every locale
- [ ] `data-testid` on every interactive and asserted visible element via
  `lib/test/test-id.ts` (no inline literals, no copy-based E2E selectors)
- [ ] Autosave and conflict handling wired if this is a clinical form
