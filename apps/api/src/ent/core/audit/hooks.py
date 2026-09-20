"""SQLAlchemy hooks that auto-audit models marked with __audit_writes__ = True."""

from __future__ import annotations

from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import get_history

from ent.core.audit.recorder import AuditRecorder
from ent.core.audit.serialize import row_to_audit_dict


_PENDING_KEY = "_ent_audit_pending"


def is_audited_model(obj: object) -> bool:
    return bool(getattr(obj.__class__, "__audit_writes__", False))


def install_audit_listeners() -> None:
    """Register once at process start; safe to call repeatedly."""

    if getattr(install_audit_listeners, "_installed", False):
        return

    @event.listens_for(Session, "before_flush")
    def _before_flush(
        session: Session,
        _flush_context: Any,
        _instances: Any,
    ) -> None:
        pending: list[tuple[str, object, dict[str, Any] | None]] = []
        for obj in session.new:
            if is_audited_model(obj):
                pending.append(("create", obj, None))
        for obj in session.dirty:
            if not is_audited_model(obj):
                continue
            if not session.is_modified(obj, include_collections=False):
                continue
            pending.append(("update", obj, _snapshot_before(obj)))
        for obj in session.deleted:
            if is_audited_model(obj):
                pending.append(("delete", obj, row_to_audit_dict(obj)))
        session.info[_PENDING_KEY] = pending

    @event.listens_for(Session, "after_flush")
    def _after_flush(session: Session, _flush_context: Any) -> None:
        pending = session.info.pop(_PENDING_KEY, [])
        if not pending:
            return
        recorder = AuditRecorder(session)
        for action, obj, before in pending:
            if action == "create":
                recorder.record_entity_create(obj)
            elif action == "update" and before is not None:
                recorder.record_entity_update(obj, before=before)
            elif action == "delete" and before is not None:
                recorder.record_entity_delete(obj, before=before)

    setattr(install_audit_listeners, "_installed", True)


def _snapshot_before(obj: object) -> dict[str, Any]:
    """Restore attribute history.deleted values onto a JSON-safe snapshot."""

    from ent.core.audit.serialize import json_safe

    current = row_to_audit_dict(obj)
    mapper = obj.__mapper__  # type: ignore[attr-defined]
    for attr in mapper.column_attrs:
        history = get_history(obj, attr.key)
        if history.deleted:
            current[attr.key] = json_safe(history.deleted[0])
    return current
