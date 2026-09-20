"""In-process event bus (expanded with worker integration in P0-07)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable

from ent.core.events.events import DomainEvent

EventHandler = Callable[[DomainEvent], Awaitable[None] | None]


class EventBus:
    """Subscribe/publish; UnitOfWork publishes only after a successful commit."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self.published: list[DomainEvent] = []

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._handlers[event_name].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        self.published.append(event)
        for handler in self._handlers.get(event.name, []):
            result = handler(event)
            if isinstance(result, Awaitable):
                await result

    def clear_published(self) -> None:
        self.published.clear()


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
