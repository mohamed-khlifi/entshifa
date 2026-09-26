from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ent.features.health.schemas.responses import (
    LiveHealthResponse,
    ReadinessCheck,
    ReadyHealthResponse,
)
from ent.integrations.mysql import ping_mysql
from ent.integrations.redis import ping_redis
from ent.integrations.storage import get_object_storage
from ent.settings import Settings


@dataclass(frozen=True, slots=True)
class HealthService:
    settings: Settings

    def live(self) -> LiveHealthResponse:
        return LiveHealthResponse(status="live")

    async def ready(self) -> tuple[ReadyHealthResponse, bool]:
        checks: list[ReadinessCheck] = []
        all_ok = True
        storage = get_object_storage(self.settings)

        async def check_mysql() -> None:
            await ping_mysql(self.settings)

        async def check_redis() -> None:
            await ping_redis(self.settings)

        probes: list[tuple[str, Callable[[], Awaitable[None]]]] = [
            ("mysql", check_mysql),
            ("redis", check_redis),
            ("storage", storage.ping),
        ]
        for name, checker in probes:
            try:
                await checker()
                checks.append(ReadinessCheck(name=name, status="ok"))
            except Exception:
                all_ok = False
                checks.append(ReadinessCheck(name=name, status="error"))

        status = "ready" if all_ok else "not_ready"
        return ReadyHealthResponse(status=status, checks=checks), all_ok
