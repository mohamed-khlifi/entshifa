"""Refuse mutations of a signed procedure, including paths that skip the service."""

from __future__ import annotations

from typing import Any

from sqlalchemy import event, text
from sqlalchemy.orm.attributes import get_history

from ent.features.procedures.constants import LOCKED_STATUSES
from ent.features.procedures.exceptions import (
    ProcedureInvalidTransitionError,
    ProcedureLockedError,
)

_AMEND_FIELDS = frozenset({"status", "version", "updated_by_id", "updated_at"})
_ADDENDUM_PARENT_STATUSES = frozenset({"signed", "amended"})


def install_procedure_guards(procedure: type[Any], addendum: type[Any]) -> None:
    """Register once, when the mappers are created."""

    event.listen(procedure, "before_update", _guard_procedure_update)
    event.listen(addendum, "before_insert", _guard_addendum_insert)
    event.listen(addendum, "before_update", _guard_addendum_update)


def _guard_procedure_update(mapper: Any, _connection: Any, target: Any) -> None:
    history = get_history(target, "status")
    previous = history.deleted[0] if history.deleted else target.status
    if previous == "draft":
        return
    if previous not in LOCKED_STATUSES:
        return
    changed = {
        attr.key
        for attr in mapper.column_attrs
        if get_history(target, attr.key).has_changes()
    }
    if not changed <= _AMEND_FIELDS:
        raise ProcedureLockedError(public_id=target.public_id, status=str(previous))
    if "status" in changed and target.status != "amended":
        raise ProcedureLockedError(public_id=target.public_id, status=str(previous))


def _guard_addendum_insert(_mapper: Any, connection: Any, target: Any) -> None:
    status = connection.execute(
        text("SELECT status FROM procedure_record WHERE id = :procedure_record_id"),
        {"procedure_record_id": int(target.procedure_record_id)},
    ).scalar_one_or_none()
    if status in _ADDENDUM_PARENT_STATUSES:
        return
    raise ProcedureInvalidTransitionError(
        from_status=str(status or "missing"),
        to_status="amended",
    )


def _guard_addendum_update(_mapper: Any, _connection: Any, target: Any) -> None:
    raise ProcedureLockedError(public_id=getattr(target, "public_id", None))
