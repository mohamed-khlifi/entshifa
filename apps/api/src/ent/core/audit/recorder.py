"""Write audit_log and access_log rows from request context."""

from __future__ import annotations

import ipaddress
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ent.core.audit.models import AccessLog, AuditLog
from ent.core.audit.serialize import changed_field_names, row_to_audit_dict
from ent.core.context import (
    get_clinic_id,
    get_ip_address,
    get_request_id,
    get_user_agent,
    get_user_id,
)
from ent.core.utils.ids import new_ulid


class AuditRecorder:
    """Records write and read events; never logs secrets or clinical free text beyond JSON snapshots."""

    def __init__(self, session: AsyncSession | Session) -> None:
        self._session = session

    def record_write(
        self,
        *,
        action: str,
        entity: object,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        changed_fields: list[str] | None = None,
        clinic_id: int | None = None,
        patient_id: int | None = None,
        reason: str | None = None,
    ) -> AuditLog:
        resolved_clinic_id = (
            clinic_id or get_clinic_id() or getattr(entity, "clinic_id", None)
        )
        if resolved_clinic_id is None:
            msg = "audit write requires clinic_id"
            raise RuntimeError(msg)

        after_payload = after if after is not None else row_to_audit_dict(entity)
        fields = changed_fields
        if fields is None and before is not None:
            fields = sorted(
                k for k in after_payload if before.get(k) != after_payload.get(k)
            )

        row = AuditLog(
            public_id=new_ulid(),
            clinic_id=int(resolved_clinic_id),
            user_id=get_user_id(),
            request_id=get_request_id(),
            action=action,
            entity_type=entity.__class__.__tablename__,  # type: ignore[attr-defined]
            entity_id=getattr(entity, "id", None),
            entity_public_id=getattr(entity, "public_id", None),
            patient_id=patient_id or getattr(entity, "patient_id", None),
            before_json=before,
            after_json=after_payload,
            changed_fields=fields,
            reason=reason,
            ip_address=_encode_ip(get_ip_address()),
            user_agent=get_user_agent(),
            occurred_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self._session.add(row)
        return row

    def record_access(
        self,
        *,
        action: str,
        entity_type: str,
        clinic_id: int | None = None,
        entity_id: int | None = None,
        entity_public_id: str | None = None,
        patient_id: int | None = None,
        reason: str | None = None,
    ) -> AccessLog:
        resolved_clinic_id = clinic_id or get_clinic_id()
        if resolved_clinic_id is None:
            msg = "access log requires clinic_id"
            raise RuntimeError(msg)

        row = AccessLog(
            public_id=new_ulid(),
            clinic_id=int(resolved_clinic_id),
            user_id=get_user_id(),
            request_id=get_request_id(),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_public_id=entity_public_id,
            patient_id=patient_id,
            before_json=None,
            after_json=None,
            changed_fields=None,
            reason=reason,
            ip_address=_encode_ip(get_ip_address()),
            user_agent=get_user_agent(),
            occurred_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self._session.add(row)
        return row

    def record_entity_create(
        self, entity: object, *, clinic_id: int | None = None
    ) -> AuditLog:
        return self.record_write(
            action="create",
            entity=entity,
            before=None,
            after=row_to_audit_dict(entity),
            changed_fields=None,
            clinic_id=clinic_id,
        )

    def record_entity_update(
        self, entity: object, *, before: dict[str, Any]
    ) -> AuditLog:
        after = row_to_audit_dict(entity)
        return self.record_write(
            action="update",
            entity=entity,
            before=before,
            after=after,
            changed_fields=changed_field_names(entity)
            or sorted(k for k in after if before.get(k) != after.get(k)),
        )

    def record_entity_delete(
        self, entity: object, *, before: dict[str, Any]
    ) -> AuditLog:
        return self.record_write(
            action="delete",
            entity=entity,
            before=before,
            after=None,
            changed_fields=sorted(before.keys()),
        )


def _encode_ip(ip_address: str | None) -> bytes | None:
    if not ip_address:
        return None
    try:
        if ":" in ip_address:
            return ipaddress.IPv6Address(ip_address).packed
        return ipaddress.IPv4Address(ip_address).packed
    except ValueError:
        return None
