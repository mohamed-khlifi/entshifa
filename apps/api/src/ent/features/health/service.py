from __future__ import annotations

from dataclasses import dataclass

from ent.features.health.schemas.responses import (
    LiveHealthResponse,
    ReadinessCheck,
    ReadyHealthResponse,
)
from ent.integrations.mysql import ping_mysql
from ent.integrations.redis import ping_redis
from ent.integrations.storage.s3 import ping_storage
from ent.settings import Settings


@dataclass(frozen=True, slots=True)
class HealthService:
    settings: Settings

    def live(self) -> LiveHealthResponse:
        return LiveHealthResponse(status="live")

    async def ready(self) -> tuple[ReadyHealthResponse, bool]:
        checks: list[ReadinessCheck] = []
        all_ok = True

        for name, checker in (
            ("mysql", ping_mysql),
            ("redis", ping_redis),
            ("storage", ping_storage),
        ):
            try:
                await checker(self.settings)
                checks.append(ReadinessCheck(name=name, status="ok"))
            except Exception:
                all_ok = False
                checks.append(ReadinessCheck(name=name, status="error"))

        status = "ready" if all_ok else "not_ready"
        return ReadyHealthResponse(status=status, checks=checks), all_ok
