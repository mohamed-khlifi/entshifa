from ent.core.schemas.base import CamelModel


class LiveHealthResponse(CamelModel):
    status: str


class ReadinessCheck(CamelModel):
    name: str
    status: str


class ReadyHealthResponse(CamelModel):
    status: str
    checks: list[ReadinessCheck]
