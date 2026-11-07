# EntShifa web

Next.js App Router frontend. Full skeleton in **P0-09** per
`docs/architecture/architecture-and-structure.txt` Part III.

## Design

Light-first, modern clinical UI: tokens in `src/styles/tokens.css`, Inter
and Noto Sans Arabic from vendored `.woff2` files (`src/assets/fonts/`, loaded
with `next/font/local`), teal/blue-gray palette, soft elevation. See
`.cursor/rules/frontend.mdc`
(Visual design).

## i18n

API error codes (e.g. `auth.invalid_credentials`) map to **nested** keys in
`messages/*/errors.json`, not flat keys containing `.`.

## Test automation

Assign every interactive and asserted visible element a `data-testid` only through
`src/lib/test/test-id.ts` (`testId`, `testIdProps`, `testIds` registry).
Playwright must not select by translated copy.
