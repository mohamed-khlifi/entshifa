# EntShifa worker

Runs background jobs and shares domain code with `apps/api`.

```powershell
# from repo root, with apps/api/.venv activated and Docker Redis/MySQL up
cd apps\api
.\.venv\Scripts\python.exe -m ent.jobs.worker

# or
cd apps\worker
..\api\.venv\Scripts\python.exe -m worker
```

Jobs live in `apps/api/src/ent/jobs/`. The worker dequeues Redis messages and
executes them through the idempotent `execute_job` runner (`job_run` table).
