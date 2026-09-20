# EntShifa web

Next.js App Router frontend. Full skeleton in **P0-09** per
`docs/architecture/architecture-and-structure.txt` Part III.

Test automation: assign every interactive and asserted visible element a
`data-testid` only through `src/lib/test/test-id.ts` (`testId`, `testIdProps`,
`testIds` registry). Playwright must not select by translated copy.
