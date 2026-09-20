"""Wire domain events to background jobs."""

from __future__ import annotations

from ent.core.events.bus import EventBus, get_event_bus
from ent.jobs.tasks import JOB_HANDLE_DOMAIN_EVENT


def wire_event_handlers(bus: EventBus | None = None) -> EventBus:
    """Idempotent registration of default event → job subscriptions."""

    target = bus or get_event_bus()
    existing = target._handlers.get("site.created", [])
    if any(sub.background_job == JOB_HANDLE_DOMAIN_EVENT for sub in existing):
        return target
    target.subscribe("site.created", background_job=JOB_HANDLE_DOMAIN_EVENT)
    return target
