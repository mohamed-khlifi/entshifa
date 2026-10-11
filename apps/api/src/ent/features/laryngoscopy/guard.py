"""Refuse laryngoscopy writes once the parent procedure has left draft."""

from __future__ import annotations

from typing import Any

from sqlalchemy import event, text
from sqlalchemy.orm.attributes import get_history

from ent.features.procedures.constants import LOCKED_STATUSES
from ent.features.procedures.exceptions import ProcedureLockedError

_INSTALLED = False


def install_laryngoscopy_guards(exam: type[Any]) -> None:
    """Register once. Observation rows are already locked by the procedure id."""

    global _INSTALLED
    if _INSTALLED:
        return
    event.listen(exam, "before_insert", _guard_exam)
    event.listen(exam, "before_update", _guard_exam)
    _INSTALLED = True


def _guard_exam(mapper: Any, connection: Any, target: Any) -> None:
    del mapper
    history = get_history(target, "procedure_record_id")
    if history.deleted:
        raise ProcedureLockedError(public_id=getattr(target, "public_id", None))
    status = connection.execute(
        text("SELECT status FROM procedure_record WHERE id = :id"),
        {"id": target.procedure_record_id},
    ).scalar()
    if status in LOCKED_STATUSES:
        raise ProcedureLockedError(
            public_id=getattr(target, "public_id", None),
            status=str(status),
        )
