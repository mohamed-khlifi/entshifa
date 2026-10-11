"""Refuse endoscopy writes once the parent procedure has left draft."""

from __future__ import annotations

from typing import Any

from sqlalchemy import event, text
from sqlalchemy.orm.attributes import get_history

from ent.features.procedures.constants import LOCKED_STATUSES
from ent.features.procedures.exceptions import ProcedureLockedError

_INSTALLED = False


def install_endoscopy_guards(exam: type[Any], observation: type[Any]) -> None:
    """Register once, when the endoscopy mapper is created."""

    global _INSTALLED
    if _INSTALLED:
        return
    event.listen(exam, "before_insert", _guard_exam)
    event.listen(exam, "before_update", _guard_exam)
    event.listen(observation, "before_insert", _guard_observation)
    event.listen(observation, "before_update", _guard_observation)
    _INSTALLED = True


def _guard_exam(mapper: Any, connection: Any, target: Any) -> None:
    del mapper
    history = get_history(target, "procedure_record_id")
    if history.deleted:
        raise ProcedureLockedError(public_id=getattr(target, "public_id", None))
    _reject_if_locked(connection, target.procedure_record_id, target)


def _guard_observation(mapper: Any, connection: Any, target: Any) -> None:
    del mapper
    procedure_id = target.procedure_record_id
    if procedure_id is None:
        return
    _reject_if_locked(connection, procedure_id, target)


def _reject_if_locked(connection: Any, procedure_id: int, target: Any) -> None:
    status = connection.execute(
        text("SELECT status FROM procedure_record WHERE id = :id"),
        {"id": procedure_id},
    ).scalar()
    if status in LOCKED_STATUSES:
        raise ProcedureLockedError(
            public_id=getattr(target, "public_id", None),
            status=str(status),
        )
