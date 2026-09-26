"""In-process event bus with optional background job enqueue (P0-07)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ent.core.events.events import DomainEvent

EventHandler = Callable[[DomainEvent], Awaitable[None] | None]


@dataclass(frozen=True, slots=True)
class _Subscription:
    handler: EventHandler | None
    background_job: str | None


class EventBus:
    """Subscribe/publish; UnitOfWork publishes only after a successful commit."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[_Subscription]] = defaultdict(list)
        self.published: list[DomainEvent] = []
        self.enqueued: list[tuple[str, str]] = []

    def subscribe(
        self,
        event_name: str,
        handler: EventHandler | None = None,
        *,
        background_job: str | None = None,
    ) -> None:
        if handler is None and background_job is None:
            msg = "subscribe requires handler and/or background_job"
            raise ValueError(msg)
        self._handlers[event_name].append(
            _Subscription(handler=handler, background_job=background_job),
        )

    async def publish(self, event: DomainEvent) -> None:
        self.published.append(event)
        for sub in self._handlers.get(event.name, []):
            if sub.background_job is not None:
                from ent.jobs.queue import enqueue_job

                public_id = event.payload.get("public_id")
                idempotency_key = (
                    f"{event.name}:{public_id or event.occurred_at.isoformat()}"
                )
                payload = {"event_name": event.name, **event.payload}
                await enqueue_job(
                    job_name=sub.background_job,
                    idempotency_key=str(idempotency_key)[:120],
                    payload=payload,
                )
                self.enqueued.append((sub.background_job, str(idempotency_key)[:120]))
            if sub.handler is not None:
                result = sub.handler(event)
                if isinstance(result, Awaitable):
                    await result

    def clear_published(self) -> None:
        self.published.clear()
        self.enqueued.clear()


_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


def reset_event_bus() -> EventBus:
    """Test helper: replace the process-wide bus."""

    global _bus
    _bus = EventBus()
    return _bus
