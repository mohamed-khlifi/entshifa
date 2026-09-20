"""Transaction boundary with post-commit event publishing."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ent.core.events.bus import EventBus, get_event_bus
from ent.core.events.events import DomainEvent


class UnitOfWork:
    """Opens a transaction, commits on success, publishes events only after commit."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        event_bus: EventBus | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._bus = event_bus or get_event_bus()
        self.session: AsyncSession | None = None
        self.events: list[DomainEvent] = []

    async def __aenter__(self) -> Self:
        self.session = self._session_factory()
        await self.session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self.session is not None
        try:
            if exc_type is not None:
                await self.session.rollback()
                self.events.clear()
            else:
                await self.session.commit()
                for event in self.events:
                    await self._bus.publish(event)
        finally:
            await self.session.close()
            self.session = None

    def emit(self, event: DomainEvent) -> None:
        self.events.append(event)

    @property
    def require_session(self) -> AsyncSession:
        if self.session is None:
            msg = "UnitOfWork session is not active"
            raise RuntimeError(msg)
        return self.session
