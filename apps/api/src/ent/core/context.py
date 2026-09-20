"""Request-scoped contextvars (architecture section 6 / P0-05)."""

from __future__ import annotations

from contextvars import ContextVar, Token

from ent.core.utils.ids import new_ulid

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[int | None] = ContextVar("user_id", default=None)
clinic_id_var: ContextVar[int | None] = ContextVar("clinic_id", default=None)
ip_address_var: ContextVar[str | None] = ContextVar("ip_address", default=None)
user_agent_var: ContextVar[str | None] = ContextVar("user_agent", default=None)


def get_request_id() -> str:
    value = request_id_var.get()
    if value:
        return value
    generated = new_ulid()
    request_id_var.set(generated)
    return generated


def set_request_id(request_id: str) -> Token[str]:
    return request_id_var.set(request_id)


def get_user_id() -> int | None:
    return user_id_var.get()


def set_user_id(user_id: int | None) -> Token[int | None]:
    return user_id_var.set(user_id)


def get_clinic_id() -> int | None:
    return clinic_id_var.get()


def set_clinic_id(clinic_id: int | None) -> Token[int | None]:
    return clinic_id_var.set(clinic_id)


def get_ip_address() -> str | None:
    return ip_address_var.get()


def set_ip_address(ip_address: str | None) -> Token[str | None]:
    return ip_address_var.set(ip_address)


def get_user_agent() -> str | None:
    return user_agent_var.get()


def set_user_agent(user_agent: str | None) -> Token[str | None]:
    return user_agent_var.set(user_agent)


def reset_context(
    *,
    request_id_token: Token[str] | None = None,
    user_token: Token[int | None] | None = None,
    clinic_token: Token[int | None] | None = None,
    ip_token: Token[str | None] | None = None,
    user_agent_token: Token[str | None] | None = None,
) -> None:
    if request_id_token is not None:
        request_id_var.reset(request_id_token)
    if user_token is not None:
        user_id_var.reset(user_token)
    if clinic_token is not None:
        clinic_id_var.reset(clinic_token)
    if ip_token is not None:
        ip_address_var.reset(ip_token)
    if user_agent_token is not None:
        user_agent_var.reset(user_agent_token)
