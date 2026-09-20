"""Job registry, retry policy, and idempotent execution."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ent.core.utils.ids import new_ulid
from ent.jobs.models import JobRun

logger = logging.getLogger(__name__)

JobCallable = Callable[..., Awaitable[dict[str, Any] | None]]

DEFAULT_MAX_ATTEMPTS = 5
MAX_BACKOFF_SECONDS = 300

_REGISTRY: dict[str, JobCallable] = {}
_MAX_ATTEMPTS: dict[str, int] = {}


def register_job(
    name: str,
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> Callable[[JobCallable], JobCallable]:
    """Decorator that registers an async job function by name."""

    def decorator(fn: JobCallable) -> JobCallable:
        _REGISTRY[name] = fn
        _MAX_ATTEMPTS[name] = max_attempts
        return fn

    return decorator


def get_job(name: str) -> JobCallable:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        msg = f"Unknown job: {name}"
        raise KeyError(msg) from exc


def max_attempts_for(name: str) -> int:
    return _MAX_ATTEMPTS.get(name, DEFAULT_MAX_ATTEMPTS)


def backoff_seconds(attempts: int) -> int:
    """Exponential backoff capped for delayed re-queue."""

    return int(min(2 ** max(attempts, 1), MAX_BACKOFF_SECONDS))


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass(frozen=True, slots=True)
class JobExecutionResult:
    job_run: JobRun
    skipped: bool
    """True when a prior success made the body a no-op."""


async def execute_job(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    job_name: str,
    idempotency_key: str,
    payload: Mapping[str, Any] | None = None,
) -> JobExecutionResult:
    """Run a job once per idempotency key; retries update the same row."""

    body = get_job(job_name)
    max_attempts = max_attempts_for(job_name)
    data = dict(payload or {})

    async with session_factory() as session:
        existing = await _get_by_key(session, idempotency_key)
        if existing is not None and existing.status in {"succeeded", "dead", "running"}:
            return JobExecutionResult(job_run=existing, skipped=True)

        if existing is None:
            run = JobRun(
                public_id=new_ulid(),
                job_name=job_name,
                idempotency_key=idempotency_key,
                status="running",
                started_at=_utcnow(),
                attempts=1,
                payload=data,
            )
            session.add(run)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raced = await _get_by_key(session, idempotency_key)
                assert raced is not None
                if raced.status in {"succeeded", "dead", "running"}:
                    return JobExecutionResult(job_run=raced, skipped=True)
                run = raced
                run.status = "running"
                run.started_at = _utcnow()
                run.attempts = int(run.attempts) + 1
                run.payload = data
                await session.commit()
        else:
            run = existing
            run.status = "running"
            run.started_at = _utcnow()
            run.finished_at = None
            run.error_text = None
            run.attempts = int(run.attempts) + 1
            run.payload = data
            await session.commit()

        run_id = run.id

    try:
        result = await body(**data)
    except Exception as exc:
        logger.exception("Job %s failed (key=%s)", job_name, idempotency_key)
        async with session_factory() as session:
            failed = await session.get(JobRun, run_id)
            assert failed is not None
            failed.error_text = str(exc)[:4000]
            if int(failed.attempts) >= max_attempts:
                failed.status = "dead"
            else:
                failed.status = "failed"
            failed.finished_at = _utcnow()
            await session.commit()
            await session.refresh(failed)
            return JobExecutionResult(job_run=failed, skipped=False)

    async with session_factory() as session:
        succeeded = await session.get(JobRun, run_id)
        assert succeeded is not None
        merged = dict(succeeded.payload or {})
        if result:
            merged["result"] = result
        succeeded.payload = merged
        succeeded.status = "succeeded"
        succeeded.finished_at = _utcnow()
        succeeded.error_text = None
        await session.commit()
        await session.refresh(succeeded)
        return JobExecutionResult(job_run=succeeded, skipped=False)


async def _get_by_key(session: AsyncSession, idempotency_key: str) -> JobRun | None:
    result = await session.execute(
        select(JobRun).where(JobRun.idempotency_key == idempotency_key),
    )
    return result.scalar_one_or_none()
