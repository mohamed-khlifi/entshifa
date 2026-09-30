"""Refuse mutations of a signed visit, including paths that skip the service."""

from __future__ import annotations

from typing import Any

from sqlalchemy import event, text
from sqlalchemy.orm.attributes import get_history

from ent.features.encounters.constants import LOCKED_STATUSES
from ent.features.encounters.exceptions import EncounterLockedError

_AMEND_FIELDS = frozenset({"status", "version", "updated_by_id", "updated_at"})


def install_encounter_guards(
    encounter: type[Any],
    complaint: type[Any],
    addendum: type[Any],
    signature: type[Any],
) -> None:
    """Register once, when the mappers are created."""

    event.listen(encounter, "before_update", _guard_encounter_update)
    event.listen(complaint, "before_insert", _guard_complaint_write)
    event.listen(complaint, "before_update", _guard_complaint_write)
    event.listen(addendum, "before_update", _guard_addendum_update)
    event.listen(signature, "before_update", _guard_signature_update)


def _guard_encounter_update(mapper: Any, _connection: Any, target: Any) -> None:
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
    if previous == "cancelled" or not changed <= _AMEND_FIELDS:
        raise EncounterLockedError(public_id=target.public_id, status=str(previous))
    if "status" in changed and target.status != "amended":
        raise EncounterLockedError(public_id=target.public_id, status=str(previous))


def _guard_complaint_write(_mapper: Any, connection: Any, target: Any) -> None:
    status = connection.execute(
        text("SELECT status FROM encounter WHERE id = :encounter_id"),
        {"encounter_id": int(target.encounter_id)},
    ).scalar_one_or_none()
    if status is None or status == "draft":
        return
    raise EncounterLockedError(status=str(status))


def _guard_addendum_update(_mapper: Any, _connection: Any, target: Any) -> None:
    raise EncounterLockedError(public_id=getattr(target, "public_id", None))


def _guard_signature_update(_mapper: Any, _connection: Any, target: Any) -> None:
    raise EncounterLockedError(public_id=getattr(target, "public_id", None))
