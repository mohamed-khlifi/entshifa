"""Worker loop: dequeue Redis messages and execute jobs idempotently."""

from __future__ import annotations

import asyncio
import logging
import signal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ent.core.db.session import dispose_engine, get_session_factory
from ent.integrations.redis import close_redis
from ent.jobs.base import backoff_seconds, execute_job
from ent.jobs.queue import dequeue_job, enqueue_job
from ent.jobs.tasks import (  # noqa: F401 — register jobs
    JOB_HANDLE_DOMAIN_EVENT,
    JOB_PING_DEPENDENCIES,
    JOB_PROCESS_ATTACHMENT,
)
from ent.settings import load_settings

logger = logging.getLogger(__name__)


async def process_one(
    session_factory: async_sessionmaker[AsyncSession],
    message: dict[str, Any],
) -> None:
    job_name = str(message["job_name"])
    idempotency_key = str(message["idempotency_key"])
    payload = message.get("payload") or {}
    if not isinstance(payload, dict):
        payload = {}

    result = await execute_job(
        session_factory,
        job_name=job_name,
        idempotency_key=idempotency_key,
        payload=payload,
    )
    run = result.job_run
    if run.status == "failed":
        delay = backoff_seconds(int(run.attempts))
        logger.warning(
            "Re-queueing failed job %s key=%s in %ss (attempt %s)",
            job_name,
            idempotency_key,
            delay,
            run.attempts,
        )
        await enqueue_job(
            job_name=job_name,
            idempotency_key=idempotency_key,
            payload=payload,
            delay_seconds=delay,
        )
    elif run.status == "dead":
        logger.error("Job %s key=%s moved to dead letter", job_name, idempotency_key)
    elif result.skipped:
        logger.info("Skipped job %s key=%s (status=%s)", job_name, idempotency_key, run.status)
    else:
        logger.info("Succeeded job %s key=%s", job_name, idempotency_key)


async def run_worker(*, once: bool = False, idle_timeout: int = 1) -> None:
    """Process queue messages until stopped (or a single message when once=True)."""

    load_settings()
    factory = get_session_factory()
    stop = asyncio.Event()

    def _stop(*_args: object) -> None:
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
        except NotImplementedError:
            # Windows: signal handlers in asyncio are limited.
            signal.signal(sig, lambda *_: _stop())

    logger.info("Worker started (once=%s)", once)
    try:
        while not stop.is_set():
            message = await dequeue_job(timeout_seconds=idle_timeout)
            if message is None:
                if once:
                    break
                continue
            await process_one(factory, message)
            if once:
                break
    finally:
        await dispose_engine()
        await close_redis()
        logger.info("Worker stopped")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
