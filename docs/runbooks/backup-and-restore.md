# Backup and restore

Clinical data lives in MySQL. Object bytes (images, PDFs) live in the
S3-compatible bucket. Restore both, or a clinic comes back with a chart that
points at missing files.

These commands assume Docker Compose is running from the repository root and
`.env` holds `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `S3_BUCKET`,
`MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD`. Do not commit the dump files.

## Backup MySQL

```bash
mkdir -p build
docker compose --env-file .env exec -T mysql \
  mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" \
  --single-transaction --routines --triggers \
  "$MYSQL_DATABASE" > build/entshifa.sql
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path build | Out-Null
$envFile = Get-Content .env | Where-Object { $_ -match '^[^#]' }
function Env([string]$name) {
  ($envFile | Where-Object { $_ -like "$name=*" } | Select-Object -First 1).Split('=', 2)[1]
}
$db = Env 'MYSQL_DATABASE'
$root = Env 'MYSQL_ROOT_PASSWORD'
docker compose --env-file .env exec -T mysql mysqldump -uroot "-p$root" --single-transaction --routines --triggers $db | Set-Content -Encoding utf8 build\entshifa.sql
```

`Set-Content` can change line endings. For a byte-exact dump on Windows, prefer
Git Bash and the bash command above.

## Backup objects

```bash
docker compose --env-file .env --profile init run --rm --entrypoint sh minio-init -c \
  "mc alias set local http://minio:9000 \"$MINIO_ROOT_USER\" \"$MINIO_ROOT_PASSWORD\" && mc mirror local/$S3_BUCKET /tmp/mirror"
```

The init container is ephemeral, so copy the bucket out with a bind mount when
you need to keep the objects:

```bash
docker compose --env-file .env run --rm --entrypoint sh \
  -v "$PWD/build/minio-mirror:/backup" minio-init -c \
  "mc alias set local http://minio:9000 \"$MINIO_ROOT_USER\" \"$MINIO_ROOT_PASSWORD\" && mc mirror local/$S3_BUCKET /backup"
```

If that service name is not running, use the MinIO console
(`http://localhost:9001`) and download the bucket.

## Restore MySQL

Restore into a new database first. Promote it only after the checks below pass.

```bash
docker compose --env-file .env exec -T mysql \
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" \
  -e "CREATE DATABASE IF NOT EXISTS entshifa_restore"
docker compose --env-file .env exec -T mysql \
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" entshifa_restore < build/entshifa.sql
```

Then point a scratch `DATABASE_URL` at `entshifa_restore`, run
`python -m alembic upgrade head` from `apps/api` (it should already be at head),
and log in with a known user from the dump.

Drop the scratch database when you are finished:

```bash
docker compose --env-file .env exec -T mysql \
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" \
  -e "DROP DATABASE entshifa_restore"
```

## Restore objects

```bash
docker compose --env-file .env run --rm --entrypoint sh \
  -v "$PWD/build/minio-mirror:/backup" minio-init -c \
  "mc alias set local http://minio:9000 \"$MINIO_ROOT_USER\" \"$MINIO_ROOT_PASSWORD\" && mc mirror /backup local/$S3_BUCKET"
```

## Anonymized copy for development

`make anonymize` (or `python -m ent.cli.anonymize` from `apps/api`) reads the
current database and writes `build/anonymized-dev.sql`. Names, phones,
identifiers and free text are replaced. Each patient's dates move by one stable
offset so intervals stay intact. Staff passwords in that file are the local
demo password hash. Do not treat that file as a backup.

## Restore drill log

| Date | Operator | Result |
|------|----------|--------|
| 2026-09-28 | local drill | See the notes below. Update this row if a later drill fails. |

Drill performed on 2026-09-28 against the local Compose MySQL 8.4 database
after `seed_system` / `seed_demo`:

1. `mysqldump --single-transaction` wrote `build/backup-drill.sql` (338,715 bytes).
2. That file was restored into a new database `entshifa_restore_drill`.
3. Row counts matched on all 40 tables (0 mismatches). The source held 12
   patient rows, 44 user rows and 3 `reference_data_version` rows.
4. `entshifa_restore_drill` was dropped. The application database was left in place.
5. `python -m ent.cli.anonymize` wrote `build/anonymized-dev.sql`. The file
   contained no `admin@demo.entshifa.local` address and no demo surname from
   `dev-seed-data.json`. It did contain `@invalid.example` replacements.
