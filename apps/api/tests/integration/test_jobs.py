"""Integration tests for event bus → queue → idempotent job execution."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.core.db.unit_of_work import UnitOfWork
from ent.core.events.bus import reset_event_bus
from ent.core.events.events import DomainEvent
from ent.core.utils.ids import new_ulid
from ent.integrations.redis import get_redis
from ent.jobs.base import execute_job
from ent.jobs.models import JobRun
from ent.jobs.queue import DELAYED_KEY, QUEUE_KEY, dequeue_job, get_side_effect_count
from ent.jobs.scheduler import SCHEDULE_CURSOR_PREFIX, tick_scheduler
from ent.jobs.tasks import JOB_HANDLE_DOMAIN_EVENT, JOB_PING_DEPENDENCIES
from ent.jobs.wiring import wire_event_handlers
from ent.jobs.worker import process_one


@pytest.fixture(autouse=True)
async def _clean_job_redis() -> None:
    client = await get_redis()
    await client.delete(QUEUE_KEY, DELAYED_KEY)
    async for key in client.scan_iter(match=f"{SCHEDULE_CURSOR_PREFIX}*"):
        await client.delete(key)
    yield
    await client.delete(QUEUE_KEY, DELAYED_KEY)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_events_publish_only_after_commit_and_enqueue_job() -> None:
    bus = reset_event_bus()
    wire_event_handlers(bus)
    factory = get_session_factory()
    public_id = new_ulid()

    with pytest.raises(RuntimeError, match="rollback"):
        async with UnitOfWork(factory, event_bus=bus) as uow:
            uow.emit(
                DomainEvent(
                    name="site.created",
                    payload={"public_id": public_id},
                ),
            )
            raise RuntimeError("rollback")

    assert bus.published == []
    assert bus.enqueued == []
    assert await dequeue_job(timeout_seconds=1) is None

    async with UnitOfWork(factory, event_bus=bus) as uow:
        uow.emit(
            DomainEvent(
                name="site.created",
                payload={"public_id": public_id},
            ),
        )

    assert len(bus.published) == 1
    assert bus.enqueued == [(JOB_HANDLE_DOMAIN_EVENT, f"site.created:{public_id}")]

    message = await dequeue_job(timeout_seconds=2)
    assert message is not None
    assert message["job_name"] == JOB_HANDLE_DOMAIN_EVENT
    assert message["idempotency_key"] == f"site.created:{public_id}"

    await process_one(factory, message)

    async with factory() as session:
        row = (
            await session.execute(
                select(JobRun).where(
                    JobRun.idempotency_key == f"site.created:{public_id}",
                ),
            )
        ).scalar_one()
        assert row.status == "succeeded"
        assert row.attempts == 1

    effect_key = f"site.created:{public_id}"
    assert await get_side_effect_count(effect_key) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rerunning_same_idempotency_key_does_not_duplicate_effect() -> None:
    factory = get_session_factory()
    key = f"idem-{new_ulid()}"
    public_id = new_ulid()
    payload = {"event_name": "site.created", "public_id": public_id}

    first = await execute_job(
        factory,
        job_name=JOB_HANDLE_DOMAIN_EVENT,
        idempotency_key=key,
        payload=payload,
    )
    assert first.skipped is False
    assert first.job_run.status == "succeeded"

    second = await execute_job(
        factory,
        job_name=JOB_HANDLE_DOMAIN_EVENT,
        idempotency_key=key,
        payload=payload,
    )
    assert second.skipped is True
    assert second.job_run.status == "succeeded"
    assert second.job_run.id == first.job_run.id

    effect_key = f"site.created:{public_id}"
    assert await get_side_effect_count(effect_key) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_failed_job_retries_then_dead_letters() -> None:
    from ent.jobs.base import register_job

    name = f"jobs.flaky_{new_ulid()[:8]}"

    @register_job(name, max_attempts=2)
    async def flaky(**_payload: object) -> dict[str, object]:
        raise RuntimeError("always fails")

    factory = get_session_factory()
    key = f"flaky-{new_ulid()}"

    first = await execute_job(factory, job_name=name, idempotency_key=key, payload={})
    assert first.job_run.status == "failed"
    assert first.job_run.attempts == 1

    second = await execute_job(factory, job_name=name, idempotency_key=key, payload={})
    assert second.job_run.status == "dead"
    assert second.job_run.attempts == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scheduler_tick_enqueues_ping_job() -> None:
    from datetime import UTC, datetime

    from ent.integrations.redis import get_redis
    from ent.jobs.scheduler import SCHEDULE_CURSOR_PREFIX

    client = await get_redis()
    await client.delete(f"{SCHEDULE_CURSOR_PREFIX}ping_dependencies")

    enqueued = await tick_scheduler(now=datetime.now(UTC))
    assert "ping_dependencies" in enqueued

    message = await dequeue_job(timeout_seconds=2)
    assert message is not None
    assert message["job_name"] == JOB_PING_DEPENDENCIES

    factory = get_session_factory()
    await process_one(factory, message)

    async with factory() as session:
        rows = (
            await session.execute(
                select(JobRun).where(JobRun.job_name == JOB_PING_DEPENDENCIES),
            )
        ).scalars().all()
        assert any(row.status == "succeeded" for row in rows)
