"""Refuse threshold edits on finalized audiograms except via allowed columns."""

from __future__ import annotations

from typing import Any

from sqlalchemy import event, text
from sqlalchemy.orm.attributes import get_history

from ent.features.audiology.exceptions import AudiogramLockedError

_FINAL_STATUS = "final"
_THRESHOLD_MUTABLE_ON_FINAL = frozenset(
    {
        "interpretation_text",
        "is_baseline",
        "baseline_audiogram_id",
        "version",
        "updated_by_id",
        "updated_at",
    }
)


def install_audiology_guards(audiogram: type[Any], threshold: type[Any]) -> None:
    event.listen(audiogram, "before_update", _guard_audiogram_update)
    event.listen(threshold, "before_insert", _guard_threshold_write)
    event.listen(threshold, "before_update", _guard_threshold_write)


def _guard_audiogram_update(mapper: Any, _connection: Any, target: Any) -> None:
    history = get_history(target, "status")
    previous = history.deleted[0] if history.deleted else target.status
    if previous != _FINAL_STATUS:
        return
    changed = {
        attr.key
        for attr in mapper.column_attrs
        if get_history(target, attr.key).has_changes()
    }
    if not changed <= _THRESHOLD_MUTABLE_ON_FINAL:
        raise AudiogramLockedError(public_id=target.public_id)


def _guard_threshold_write(_mapper: Any, connection: Any, target: Any) -> None:
    status = connection.execute(
        text("SELECT status FROM audiogram WHERE id = :id"),
        {"id": int(target.audiogram_id)},
    ).scalar_one_or_none()
    if status == _FINAL_STATUS:
        raise AudiogramLockedError(public_id=getattr(target, "public_id", None))
