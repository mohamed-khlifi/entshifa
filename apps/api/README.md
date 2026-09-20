# EntShifa API

FastAPI backend. Application code lives under `src/ent/` per
`docs/architecture/architecture-and-structure.txt` section 4.

## Local run (P0-02 / P0-03)

From the repository root, start infrastructure (`make dev` or Docker Compose), then:

```bash
cd apps/api
py -3.12 -m venv .venv --clear   # Windows: requires Python 3.12 (see py --list)
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Use **Docker MySQL** from the repo root (`make dev` / `docker compose`), not XAMPP/phpMyAdmin.
Stop XAMPP MySQL if port `3306` is already in use. Set `MYSQL_HOST=127.0.0.1` in the root
`.env` on Windows so the API does not hit another server on `localhost` (IPv6).

`aiomysql` needs the `cryptography` package for MySQL 8 authentication (included in
`pyproject.toml`).

Load environment from the repo-root `.env` (copy from `.env.example` if needed).
The API reads `../../.env` automatically.

Apply the identity/tenancy schema (P0-03):

```bash
# from repo root with apps/api venv activated, or:
cd apps/api && python -m alembic upgrade head
# or: make migrate
```

Downgrade:

```bash
cd apps/api && python -m alembic downgrade base
# or: make migrate-down
```

```bash
uvicorn ent.main:create_app --factory --reload --host 0.0.0.0 --port 8000 --app-dir src
```

Health checks:

- `GET http://localhost:8000/health/live` — process up
- `GET http://localhost:8000/health/ready` — MySQL, Redis, and object storage

Auth (P0-04), after migrations and with the API running:

- `POST /api/v1/auth/login` — JSON `{ "email", "password" }`; returns `accessToken`, sets HttpOnly refresh cookie
- `POST /api/v1/auth/refresh` — rotates refresh cookie, returns new access token
- `POST /api/v1/auth/logout` — revokes session
- `GET /api/v1/auth/me` — requires `Authorization: Bearer …` and `auth.session.read`

Active clinic is stored on the session (never taken from the login body). Optional header
`X-Clinic-Id` switches among clinics the user belongs to.

Local demo users (after `python -m ent.cli.seed` or `make seed` from repo root with venv):

- Email: `admin@demo.entshifa.local` (and `doctor1@…`, `assistant1@…`, etc.)
- Password: `LocalDevSeed1!`

## Tests

```bash
pytest
pytest -m "not integration"   # unit only
pytest -m integration         # requires Docker MySQL (migrations, concurrent ULID)
```
