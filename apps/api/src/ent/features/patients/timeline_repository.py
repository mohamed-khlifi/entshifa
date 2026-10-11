"""One indexed read of a patient's longitudinal events (P2-11)."""

from __future__ import annotations

import base64
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import (
    String,
    and_,
    case,
    cast,
    collate,
    func,
    literal,
    null,
    or_,
    select,
    union_all,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import CompoundSelect, Select

from ent.core.db.mysql_types import unsigned_bigint
from ent.core.repository.pagination import Page
from ent.features.attachments.models import Attachment
from ent.features.diagnoses.models import Diagnosis
from ent.features.documents.models import Document
from ent.features.encounters.constants import ENCOUNTER_TYPES
from ent.features.encounters.models import Encounter
from ent.features.patients.models import PatientProblem
from ent.features.prescriptions.models import Prescription
from ent.features.recalls.models import Recall, RecallAction
from ent.features.scheduling.models import Appointment

TIMELINE_EVENT_TYPES = (
    *ENCOUNTER_TYPES,
    "diagnosis",
    "prescription",
    "document",
    "appointment",
    "no_show",
    "attachment",
    "recall",
    "phone_call",
    "recall_sent",
)

_NULL_STR = collate(cast(null(), String(255)), "utf8mb4_0900_ai_ci")
_NULL_ID = collate(cast(null(), String(26)), "utf8mb4_0900_as_cs")
_NULL_INT = cast(null(), unsigned_bigint())
_VISIT = frozenset(ENCOUNTER_TYPES)


@dataclass(frozen=True, slots=True)
class TimelineEntry:
    event_type: str
    occurred_at: datetime
    public_id: str
    status: str
    category: str | None
    laterality: str | None
    detail_text: str | None
    concept_id: int | None
    encounter_public_id: str | None


def encode_timeline_cursor(
    occurred_at: datetime, event_type: str, public_id: str
) -> str:
    raw = f"{occurred_at.isoformat()}|{event_type}|{public_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode_timeline_cursor(value: str) -> tuple[datetime, str, str]:
    padded = value + ("=" * (-len(value) % 4))
    raw = base64.urlsafe_b64decode(padded.encode()).decode()
    occurred_raw, event_type, public_id = raw.split("|", 2)
    return datetime.fromisoformat(occurred_raw), event_type, public_id


class PatientTimelineRepository:
    """Union of event tables. Each branch is filtered by clinic and patient."""

    def __init__(self, session: AsyncSession, clinic_id: int) -> None:
        self.session = session
        self.clinic_id = clinic_id

    async def page(
        self,
        *,
        patient_id: int,
        types: frozenset[str] | None,
        laterality: str | None,
        problem: PatientProblem | None,
        limit: int,
        cursor: tuple[datetime, str, str] | None,
    ) -> Page[TimelineEntry]:
        combined = self._union(
            patient_id=patient_id,
            types=types,
            laterality=laterality,
            problem=problem,
        )
        if combined is None:
            return Page(items=[], total=0, limit=limit, offset=0, next_cursor=None)
        events = combined.subquery("timeline_events")
        total = (
            await self.session.execute(select(func.count()).select_from(events))
        ).scalar_one()
        stmt = select(events).order_by(
            events.c.occurred_at.desc(),
            events.c.event_type.desc(),
            events.c.public_id.desc(),
        )
        if cursor is not None:
            occurred_at, event_type, public_id = cursor
            stmt = stmt.where(
                or_(
                    events.c.occurred_at < occurred_at,
                    and_(
                        events.c.occurred_at == occurred_at,
                        events.c.event_type < event_type,
                    ),
                    and_(
                        events.c.occurred_at == occurred_at,
                        events.c.event_type == event_type,
                        events.c.public_id < public_id,
                    ),
                )
            )
        rows = (await self.session.execute(stmt.limit(limit + 1))).mappings().all()
        has_more = len(rows) > limit
        visible = rows[:limit]
        items = [_entry(dict(row)) for row in visible]
        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = encode_timeline_cursor(
                last.occurred_at, last.event_type, last.public_id
            )
        return Page(
            items=items,
            total=int(total or 0),
            limit=limit,
            offset=0,
            next_cursor=next_cursor,
        )

    def _union(
        self,
        *,
        patient_id: int,
        types: frozenset[str] | None,
        laterality: str | None,
        problem: PatientProblem | None,
    ) -> Select[Any] | CompoundSelect[Any] | None:
        branches: list[Select[Any]] = []
        related = self._related_encounters(patient_id, laterality, problem)
        restricted = laterality is not None or problem is not None

        visits = [name for name in ENCOUNTER_TYPES if _wanted(types, name)]
        if visits:
            branches.append(
                self._encounters(patient_id, visits, related if restricted else None)
            )
        if _wanted(types, "diagnosis"):
            branches.append(
                self._diagnoses(patient_id, laterality, problem, related, restricted)
            )
        if _wanted(types, "prescription"):
            branches.append(self._prescriptions(patient_id, related, restricted))
        if _wanted(types, "document"):
            branches.append(self._documents(patient_id, related, restricted))
        if _wanted(types, "appointment") or _wanted(types, "no_show"):
            branches.append(self._appointments(patient_id, types, related, restricted))
        if _wanted(types, "attachment"):
            branches.append(
                self._attachments(patient_id, laterality, related, restricted)
            )
        if _wanted(types, "recall"):
            branches.append(self._recalls(patient_id, laterality, related, restricted))
        if _wanted(types, "phone_call") or _wanted(types, "recall_sent"):
            branches.append(
                self._recall_actions(patient_id, types, related, restricted)
            )
        if not branches:
            return None
        if len(branches) == 1:
            return branches[0]
        return union_all(*branches)

    def _related_encounters(
        self,
        patient_id: int,
        laterality: str | None,
        problem: PatientProblem | None,
    ) -> Select[tuple[int]]:
        stmt = select(Diagnosis.encounter_id).where(
            Diagnosis.clinic_id == self.clinic_id,
            Diagnosis.patient_id == patient_id,
            Diagnosis.deleted_at.is_(None),
        )
        if problem is not None:
            stmt = stmt.where(
                or_(
                    Diagnosis.promoted_to_problem_id == problem.id,
                    and_(
                        Diagnosis.concept_id == problem.diagnosis_concept_id,
                        Diagnosis.laterality == problem.laterality,
                    ),
                )
            )
        if laterality is not None:
            stmt = stmt.where(Diagnosis.laterality.in_((laterality, "bilateral")))
        return stmt

    def _encounters(
        self,
        patient_id: int,
        visits: list[str],
        related: Select[tuple[int]] | None,
    ) -> Select[Any]:
        stmt = select(
            Encounter.encounter_type.label("event_type"),
            Encounter.started_at.label("occurred_at"),
            Encounter.public_id.label("public_id"),
            Encounter.status.label("status"),
            _NULL_STR.label("category"),
            _NULL_STR.label("laterality"),
            Encounter.chief_complaint_summary.label("detail_text"),
            _NULL_INT.label("concept_id"),
            _NULL_ID.label("encounter_public_id"),
        ).where(
            Encounter.clinic_id == self.clinic_id,
            Encounter.patient_id == patient_id,
            Encounter.deleted_at.is_(None),
            Encounter.encounter_type.in_(visits),
        )
        if related is not None:
            stmt = stmt.where(Encounter.id.in_(related))
        return stmt

    def _diagnoses(
        self,
        patient_id: int,
        laterality: str | None,
        problem: PatientProblem | None,
        related: Select[tuple[int]],
        restricted: bool,
    ) -> Select[Any]:
        stmt = (
            select(
                literal("diagnosis").label("event_type"),
                Diagnosis.effective_at.label("occurred_at"),
                Diagnosis.public_id.label("public_id"),
                Diagnosis.status.label("status"),
                _NULL_STR.label("category"),
                Diagnosis.laterality.label("laterality"),
                Diagnosis.note.label("detail_text"),
                Diagnosis.concept_id.label("concept_id"),
                collate(Encounter.public_id, "utf8mb4_0900_as_cs").label(
                    "encounter_public_id"
                ),
            )
            .join(Encounter, Encounter.id == Diagnosis.encounter_id)
            .where(
                Diagnosis.clinic_id == self.clinic_id,
                Diagnosis.patient_id == patient_id,
                Diagnosis.deleted_at.is_(None),
                Encounter.deleted_at.is_(None),
                Encounter.clinic_id == self.clinic_id,
            )
        )
        if laterality is not None:
            stmt = stmt.where(Diagnosis.laterality.in_((laterality, "bilateral")))
        if problem is not None:
            stmt = stmt.where(Diagnosis.encounter_id.in_(related))
        _ = restricted
        return stmt

    def _prescriptions(
        self,
        patient_id: int,
        related: Select[tuple[int]],
        restricted: bool,
    ) -> Select[Any]:
        stmt = select(
            literal("prescription").label("event_type"),
            func.coalesce(Prescription.issued_at, Prescription.created_at).label(
                "occurred_at"
            ),
            Prescription.public_id.label("public_id"),
            Prescription.status.label("status"),
            _NULL_STR.label("category"),
            _NULL_STR.label("laterality"),
            _NULL_STR.label("detail_text"),
            _NULL_INT.label("concept_id"),
            _NULL_ID.label("encounter_public_id"),
        ).where(
            Prescription.clinic_id == self.clinic_id,
            Prescription.patient_id == patient_id,
            Prescription.deleted_at.is_(None),
        )
        if restricted:
            stmt = stmt.where(Prescription.encounter_id.in_(related))
        return stmt

    def _documents(
        self,
        patient_id: int,
        related: Select[tuple[int]],
        restricted: bool,
    ) -> Select[Any]:
        stmt = select(
            literal("document").label("event_type"),
            Document.created_at.label("occurred_at"),
            Document.public_id.label("public_id"),
            Document.status.label("status"),
            Document.category.label("category"),
            _NULL_STR.label("laterality"),
            Document.title.label("detail_text"),
            _NULL_INT.label("concept_id"),
            _NULL_ID.label("encounter_public_id"),
        ).where(
            Document.clinic_id == self.clinic_id,
            Document.patient_id == patient_id,
            Document.deleted_at.is_(None),
        )
        if restricted:
            stmt = stmt.where(Document.encounter_id.in_(related))
        return stmt

    def _appointments(
        self,
        patient_id: int,
        types: frozenset[str] | None,
        related: Select[tuple[int]],
        restricted: bool,
    ) -> Select[Any]:
        event_type = case(
            (Appointment.status == "no_show", literal("no_show")),
            else_=literal("appointment"),
        )
        stmt = select(
            event_type.label("event_type"),
            Appointment.starts_at.label("occurred_at"),
            Appointment.public_id.label("public_id"),
            Appointment.status.label("status"),
            _NULL_STR.label("category"),
            _NULL_STR.label("laterality"),
            Appointment.reason_text.label("detail_text"),
            _NULL_INT.label("concept_id"),
            _NULL_ID.label("encounter_public_id"),
        ).where(
            Appointment.clinic_id == self.clinic_id,
            Appointment.patient_id == patient_id,
            Appointment.deleted_at.is_(None),
        )
        if types is not None:
            allowed: list[str] = []
            if "appointment" in types:
                allowed.append("appointment")
            if "no_show" in types:
                allowed.append("no_show")
            stmt = stmt.where(event_type.in_(allowed))
        if restricted:
            booked = select(Encounter.appointment_id).where(
                Encounter.clinic_id == self.clinic_id,
                Encounter.deleted_at.is_(None),
                Encounter.id.in_(related),
                Encounter.appointment_id.is_not(None),
            )
            from_recall = select(Recall.id).where(
                Recall.clinic_id == self.clinic_id,
                Recall.deleted_at.is_(None),
                Recall.patient_id == patient_id,
                Recall.source_id.in_(related),
            )
            stmt = stmt.where(
                or_(
                    Appointment.id.in_(booked),
                    Appointment.created_from_recall_id.in_(from_recall),
                )
            )
        return stmt

    def _attachments(
        self,
        patient_id: int,
        laterality: str | None,
        related: Select[tuple[int]],
        restricted: bool,
    ) -> Select[Any]:
        stmt = select(
            literal("attachment").label("event_type"),
            func.coalesce(Attachment.captured_at, Attachment.created_at).label(
                "occurred_at"
            ),
            Attachment.public_id.label("public_id"),
            literal("recorded").label("status"),
            Attachment.category.label("category"),
            Attachment.laterality.label("laterality"),
            Attachment.filename.label("detail_text"),
            _NULL_INT.label("concept_id"),
            _NULL_ID.label("encounter_public_id"),
        ).where(
            Attachment.clinic_id == self.clinic_id,
            Attachment.patient_id == patient_id,
            Attachment.deleted_at.is_(None),
        )
        if laterality is not None:
            stmt = stmt.where(Attachment.laterality.in_((laterality, "bilateral")))
        if restricted and laterality is None:
            stmt = stmt.where(Attachment.encounter_id.in_(related))
        return stmt

    def _recalls(
        self,
        patient_id: int,
        laterality: str | None,
        related: Select[tuple[int]],
        restricted: bool,
    ) -> Select[Any]:
        stmt = select(
            literal("recall").label("event_type"),
            Recall.created_at.label("occurred_at"),
            Recall.public_id.label("public_id"),
            Recall.status.label("status"),
            Recall.action_type.label("category"),
            Recall.laterality.label("laterality"),
            Recall.reason_text.label("detail_text"),
            _NULL_INT.label("concept_id"),
            _NULL_ID.label("encounter_public_id"),
        ).where(
            Recall.clinic_id == self.clinic_id,
            Recall.patient_id == patient_id,
            Recall.deleted_at.is_(None),
        )
        if laterality is not None:
            stmt = stmt.where(Recall.laterality.in_((laterality, "bilateral")))
        if restricted and laterality is None:
            stmt = stmt.where(Recall.source_id.in_(related))
        return stmt

    def _recall_actions(
        self,
        patient_id: int,
        types: frozenset[str] | None,
        related: Select[tuple[int]],
        restricted: bool,
    ) -> Select[Any]:
        event_type = case(
            (RecallAction.action == "call", literal("phone_call")),
            else_=literal("recall_sent"),
        )
        stmt = (
            select(
                event_type.label("event_type"),
                RecallAction.performed_at.label("occurred_at"),
                RecallAction.public_id.label("public_id"),
                func.coalesce(RecallAction.outcome, literal("logged")).label("status"),
                RecallAction.action.label("category"),
                Recall.laterality.label("laterality"),
                RecallAction.note.label("detail_text"),
                _NULL_INT.label("concept_id"),
                _NULL_ID.label("encounter_public_id"),
            )
            .join(Recall, Recall.id == RecallAction.recall_id)
            .where(
                RecallAction.clinic_id == self.clinic_id,
                RecallAction.deleted_at.is_(None),
                Recall.clinic_id == self.clinic_id,
                Recall.patient_id == patient_id,
                Recall.deleted_at.is_(None),
                RecallAction.action.in_(("call", "sms", "email", "whatsapp")),
            )
        )
        if types is not None:
            allowed = [name for name in ("phone_call", "recall_sent") if name in types]
            stmt = stmt.where(event_type.in_(allowed))
        if restricted:
            stmt = stmt.where(Recall.source_id.in_(related))
        return stmt


def _wanted(types: frozenset[str] | None, name: str) -> bool:
    return types is None or name in types


def _entry(row: Mapping[str, Any]) -> TimelineEntry:
    concept = row["concept_id"]
    occurred = row["occurred_at"]
    if not isinstance(occurred, datetime):
        raise TypeError("timeline occurred_at")
    return TimelineEntry(
        event_type=str(row["event_type"]),
        occurred_at=occurred,
        public_id=str(row["public_id"]),
        status=str(row["status"]),
        category=_optional_str(row["category"]),
        laterality=_optional_str(row["laterality"]),
        detail_text=_optional_str(row["detail_text"]),
        concept_id=int(concept) if concept is not None else None,
        encounter_public_id=_optional_str(row["encounter_public_id"]),
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
