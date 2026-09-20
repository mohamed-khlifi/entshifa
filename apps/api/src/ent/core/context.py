"""Request-scoped context (expanded in P0-05)."""

from __future__ import annotations

import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    value = request_id_var.get()
    if value:
        return value
    return str(uuid.uuid4())


def set_request_id(request_id: str) -> None:
    request_id_var.set(request_id)
