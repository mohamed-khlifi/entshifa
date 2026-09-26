# @entshifa/i18n-messages

Canonical UI translation catalogs for the EntShifa web app (next-intl).

## Layout

```
en/   English (default / source of truth for keys)
fr/   French
ar/   Arabic (RTL; placeholder quality until clinical review)
```

One JSON file per feature/namespace per locale (`common.json`, `auth.json`, …).
Keys are nested and semantic; never put `.` inside a JSON object key.

Consumed by `apps/web/src/lib/i18n/request.ts`.

## Checks

From the repository root:

```bash
make i18n-check
# or
node packages/i18n-messages/scripts/check.mjs
```

The script enforces: every key in every locale, no extra keys, matching
placeholder sets, and no catalog keys unused by `apps/web/src`.
