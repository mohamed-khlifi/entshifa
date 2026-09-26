"""Cron-style schedule definitions and a tick that enqueues due jobs."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from ent.core.utils.ids import new_ulid
from ent.integrations.redis import get_redis
from ent.jobs.queue import enqueue_job
from ent.jobs.tasks import JOB_PING_DEPENDENCIES

logger = logging.getLogger(__name__)

SCHEDULE_CURSOR_PREFIX = "ent:jobs:schedule:"


@dataclass(frozen=True, slots=True)
class Schedule:
    name: str
    interval: timedelta
    job_name: str
    payload: dict[str, str]


# Architecture section 9 schedules, represented as intervals for Phase 0.
# Full cron expressions arrive with ops tooling later; intervals keep ticks testable.
SCHEDULES: tuple[Schedule, ...] = (
    Schedule(
        name="ping_dependencies",
        interval=timedelta(minutes=5),
        job_name=JOB_PING_DEPENDENCIES,
        payload={"note": "scheduler"},
    ),
)


async def tick_scheduler(*, now: datetime | None = None) -> list[str]:
    """Enqueue any schedule whose interval has elapsed since the last tick."""

    moment = now or datetime.now(UTC)
    if moment.tzinfo is not None:
        moment = moment.replace(tzinfo=None)

    client = await get_redis()
    enqueued: list[str] = []
    for schedule in SCHEDULES:
        cursor_key = f"{SCHEDULE_CURSOR_PREFIX}{schedule.name}"
        last_raw = await client.get(cursor_key)
        due = True
        if last_raw is not None:
            last = datetime.fromisoformat(last_raw)
            due = moment - last >= schedule.interval
        if not due:
            continue
        idempotency_key = (
            f"schedule:{schedule.name}:{moment.strftime('%Y%m%d%H%M')}:{new_ulid()[:8]}"
        )
        await enqueue_job(
            job_name=schedule.job_name,
            idempotency_key=idempotency_key,
            payload=dict(schedule.payload),
        )
        await client.set(cursor_key, moment.isoformat(timespec="seconds"))
        enqueued.append(schedule.name)
        logger.info("Scheduler enqueued %s as %s", schedule.name, schedule.job_name)
    return enqueued
