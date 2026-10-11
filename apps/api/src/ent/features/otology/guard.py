"""Refuse otology writes once the parent procedure has left draft."""

from __future__ import annotations

from typing import Any

from sqlalchemy import event, text
from sqlalchemy.orm.attributes import get_history

from ent.features.procedures.constants import LOCKED_STATUSES
from ent.features.procedures.exceptions import ProcedureLockedError

_INSTALLED = False


def install_otology_guards(*targets: type[Any]) -> None:
    """Register once. Ear-device status changes stay editable after signing."""

    global _INSTALLED
    if _INSTALLED:
        return
    for target in targets:
        event.listen(target, "before_insert", _guard)
        event.listen(target, "before_update", _guard)
    _INSTALLED = True


def _guard(mapper: Any, connection: Any, target: Any) -> None:
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
