"""Wire domain events to background jobs."""

from __future__ import annotations

from ent.core.events.bus import EventBus, get_event_bus
from ent.features.procedures.events import PROCEDURE_PERFORMED
from ent.features.recalls.handlers import handle_procedure_performed
from ent.jobs.tasks import JOB_HANDLE_DOMAIN_EVENT


def wire_event_handlers(bus: EventBus | None = None) -> EventBus:
    """Idempotent registration of default event → job subscriptions."""

    target = bus or get_event_bus()
    existing = target._handlers.get("site.created", [])
    if not any(sub.background_job == JOB_HANDLE_DOMAIN_EVENT for sub in existing):
        target.subscribe("site.created", background_job=JOB_HANDLE_DOMAIN_EVENT)
    proc_existing = target._handlers.get(PROCEDURE_PERFORMED, [])
    if not any(sub.handler == handle_procedure_performed for sub in proc_existing):
        target.subscribe(PROCEDURE_PERFORMED, handler=handle_procedure_performed)
    return target
