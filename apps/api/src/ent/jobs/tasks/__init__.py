"""Concrete background jobs."""

from __future__ import annotations

from typing import Any

from ent.integrations.redis import ping_redis
from ent.jobs.base import register_job
from ent.jobs.queue import record_side_effect
from ent.jobs.tasks.process_attachment import (  # noqa: F401 — register job
    JOB_PROCESS_ATTACHMENT,
    process_attachment,
)
from ent.settings import get_settings

JOB_HANDLE_DOMAIN_EVENT = "jobs.handle_domain_event"
JOB_PING_DEPENDENCIES = "jobs.ping_dependencies"

__all__ = [
    "JOB_HANDLE_DOMAIN_EVENT",
    "JOB_PING_DEPENDENCIES",
    "JOB_PROCESS_ATTACHMENT",
    "handle_domain_event",
    "ping_dependencies",
    "process_attachment",
]


@register_job(JOB_HANDLE_DOMAIN_EVENT, max_attempts=5)
async def handle_domain_event(
    *,
    event_name: str,
    public_id: str | None = None,
    **_extra: Any,
) -> dict[str, Any]:
    """Record that a domain event was processed (idempotent via job runner)."""

    effect_key = f"{event_name}:{public_id or 'none'}"
    count = await record_side_effect(effect_key)
    return {
        "event_name": event_name,
        "public_id": public_id,
        "effect_count": count,
    }


@register_job(JOB_PING_DEPENDENCIES, max_attempts=3)
async def ping_dependencies(*, note: str = "scheduler") -> dict[str, Any]:
    """Real job: verify Redis is reachable. Used by the scheduler tick."""

    await ping_redis(get_settings())
    count = await record_side_effect(f"ping:{note}")
    return {"ok": True, "note": note, "effect_count": count}
