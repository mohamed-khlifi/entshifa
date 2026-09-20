# EntShifa API

FastAPI backend. Application code lives under `src/ent/` per
`docs/architecture/architecture-and-structure.txt` section 4.

## Local run (P0-02)

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

```bash
uvicorn ent.main:create_app --factory --reload --host 0.0.0.0 --port 8000 --app-dir src
```

Health checks:

- `GET http://localhost:8000/health/live` — process up
- `GET http://localhost:8000/health/ready` — MySQL, Redis, and object storage

## Tests

```bash
pytest
pytest -m integration   # requires Docker stack running
```
