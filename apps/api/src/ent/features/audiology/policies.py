"""Audiology authorization rules (technician enter vs doctor interpret)."""

from __future__ import annotations

from ent.core.errors.exceptions import PermissionDeniedError
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser


def assert_can_interpret(user: CurrentUser) -> None:
    if Permission.AUDIOLOGY_INTERPRET.value not in user.permissions:
        raise PermissionDeniedError()


def assert_interpret_fields(
    user: CurrentUser,
    *,
    interpretation_text: str | None,
    is_baseline: bool | None,
) -> None:
    if interpretation_text is not None and interpretation_text.strip():
        assert_can_interpret(user)
    if is_baseline is True:
        assert_can_interpret(user)
