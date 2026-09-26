# @entshifa/contracts

Generated OpenAPI specification and TypeScript types for the EntShifa API.

## Contents

| Path | Role |
|------|------|
| `openapi.json` | Canonical OpenAPI 3 document exported from FastAPI |
| `generated/schema.ts` | TypeScript types from that document (`openapi-typescript`) |

Do not edit generated files by hand.

## Commands

From the repository root (requires a valid `.env` so the API settings load):

```bash
make contracts        # export OpenAPI + generate TypeScript
make contracts-check  # fail if committed artifacts disagree with the code
```

Or:

```bash
cd apps/api && python -m ent.cli.export_openapi
cd packages/contracts && npm run generate
node packages/contracts/scripts/check.mjs
```

## Frontend usage

Import wire types through `apps/web/src/lib/api/generated` (friendly aliases over
`components['schemas'][...]`). Feature API modules must not hand-write response
types.
