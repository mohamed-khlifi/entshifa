"""Prescription use cases (P2-08). Dosing numbers come from formulary rows."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.core.events.bus import get_event_bus
from ent.core.schemas.base import PageMeta, PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.engines.documents.age import completed_age
from ent.engines.prescriptions.errors import EngineInputError
from ent.engines.prescriptions.pediatric_dosing import (
    DosingRule,
    PediatricDoseInput,
    applicable_max_mg_per_day,
    weight_based_dose,
)
from ent.engines.prescriptions.safety import (
    SafetyAlert,
    SafetyInput,
    SafetyItem,
    check_safety,
)
from ent.engines.prescriptions.steroid_taper import (
    TaperDay,
    TaperInput,
    generate_steroid_taper,
)
from ent.engines.results import CalculationResult
from ent.features.encounters.exceptions import EncounterNotFoundError
from ent.features.encounters.models import Encounter
from ent.features.encounters.references import EncounterReferences
from ent.features.encounters.repository import EncounterRepository
from ent.features.patients.models import Patient, PatientMedication
from ent.features.patients.repository import (
    PatientAllergyRepository,
    PatientFlagRepository,
    PatientMedicationRepository,
    PatientProblemRepository,
    PatientRepository,
)
from ent.features.prescriptions.constants import (
    HEARING_LOSS_CODE_PREFIXES,
    OVERRIDABLE_ALERTS,
    SAFETY_CONTEXT_LIMIT,
)
from ent.features.prescriptions.events import (
    PRESCRIPTION_CANCELLED,
    PRESCRIPTION_DRAFTED,
    PRESCRIPTION_ISSUED,
    prescription_event,
)
from ent.features.prescriptions.exceptions import (
    FormularyEntryNotFoundError,
    PrescriptionBlockedError,
    PrescriptionDosingInputError,
    PrescriptionDosingRuleError,
    PrescriptionIdempotencyMismatchError,
    PrescriptionInvalidStatusError,
    PrescriptionNotFoundError,
    PrescriptionVersionConflictError,
)
from ent.features.prescriptions.mapping import (
    calculation_read,
    drug_read,
    formulary_read,
    prescription_read,
    template_read,
)
from ent.features.prescriptions.models import (
    CalculationResultRow,
    FormularyEntry,
    Prescription,
    PrescriptionItem,
    PrescriptionRequestIdempotency,
    PrescriptionTemplate,
)
from ent.features.prescriptions.repository import (
    CalculationResultRepository,
    DrugFormRepository,
    DrugRepository,
    FormularyRepository,
    PrescriptionIdempotencyRepository,
    PrescriptionRepository,
    PrescriptionTemplateRepository,
)
from ent.features.prescriptions.schemas.internal import (
    DosingDocumentError,
    ParsedDosing,
    as_dosing_rule,
    parse_dosing_document,
)
from ent.features.prescriptions.schemas.requests import (
    FormularyEntryCreate,
    FormularyEntryUpdate,
    OverrideCode,
    PediatricDoseRequest,
    PrescriptionCreate,
    PrescriptionItemWrite,
    PrescriptionTemplateCreate,
    PrescriptionUpdate,
    SafetyCheckRequest,
    SafetyOverrideWrite,
    TaperRequest,
    dosing_rules_document,
)
from ent.features.prescriptions.schemas.responses import (
    CalculationRead,
    DrugRead,
    FormularyEntryRead,
    PrescriptionRead,
    PrescriptionTemplateRead,
    SafetyAlertRead,
)

_CREATE = "prescription.create"


@dataclass(frozen=True, slots=True)
class _Prepared:
    body: PrescriptionItemWrite
    formulary: FormularyEntry | None
    dose_amount: Decimal | None
    dose_unit: str | None
    volume_ml: Decimal | None
    taper: tuple[TaperDay, ...] | None
    dosing: CalculationResult | None
    taper_result: CalculationResult | None
    weight_based: bool
    allergy_ids: frozenset[str]
    drug_class: str | None
    is_ototoxic: bool
    pregnancy_category: str | None
    max_daily_mg: Decimal | None


class PrescriptionService:
    """Draft, issue, and cancel a prescription. Safety runs before every write."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = EncounterReferences(session)
        self._allergy_ids: frozenset[str] = frozenset()
        self._classes: frozenset[str] = frozenset()
        self._hearing_loss = False
        self._pregnant = False
        self._breastfeeding = False

    async def create(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        body: PrescriptionCreate,
        content_locale: str,
        idempotency_key: str | None,
    ) -> PrescriptionRead:
        self._bind(user)
        replay = await self._replay(user, idempotency_key, body)
        if replay is not None:
            return await self.get(
                user=user, public_id=replay, content_locale=content_locale
            )
        patient = await self._refs.patient(user, patient_public_id)
        encounter = await self._draft_encounter(user, body.encounter_public_id, patient)
        await self._load_chart(user, patient)
        prepared = await self._prepare(
            user, patient, body.items, body.weight_kg, body.is_pediatric
        )
        alerts = self._alerts_for(prepared, body.is_pediatric, body.weight_kg)
        self._refuse_blocks(prepared, alerts)
        row = await self._insert(user, patient, encounter, body, prepared, alerts)
        await self._store_idempotency(user, idempotency_key, body, row.public_id)
        await get_event_bus().publish(
            prescription_event(
                PRESCRIPTION_DRAFTED,
                prescription_public_id=row.public_id,
                clinic_id=user.clinic_id,
                patient_public_id=patient.public_id,
            )
        )
        loaded = await self._require(user, row.public_id)
        return await self._read(
            user, loaded, patient.public_id, encounter.public_id, content_locale
        )

    async def update(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: PrescriptionUpdate,
        content_locale: str,
    ) -> PrescriptionRead:
        self._bind(user)
        row = await self._require(user, public_id)
        if row.status != "draft":
            raise PrescriptionInvalidStatusError(status=row.status)
        if int(row.version) != body.version:
            raise PrescriptionVersionConflictError(
                server_version=int(row.version), client_version=body.version
            )
        if body.items is None:
            raise ValidationError(reason="items_required")
        patient = await self._patient(user, int(row.patient_id))
        encounter_public_id = await self._encounter_public_id(user, row)
        encounter = await self._draft_encounter(user, encounter_public_id, patient)
        is_pediatric = (
            row.is_pediatric if body.is_pediatric is None else body.is_pediatric
        )
        weight = row.weight_kg_at_issue if body.weight_kg is None else body.weight_kg
        await self._load_chart(user, patient)
        prepared = await self._prepare(
            user, patient, body.items, weight, bool(is_pediatric)
        )
        alerts = self._alerts_for(prepared, bool(is_pediatric), weight)
        self._refuse_blocks(prepared, alerts)
        await self._replace_items(user, row, prepared)
        row.locale = body.locale or row.locale
        row.is_pediatric = bool(is_pediatric) or any(
            item.weight_based for item in prepared
        )
        row.weight_kg_at_issue = weight
        if body.notes is not None:
            row.notes = body.notes
        row.safety_alerts = _alert_payload(alerts)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.flush()
        loaded = await self._require(user, public_id)
        return await self._read(
            user, loaded, patient.public_id, encounter.public_id, content_locale
        )

    async def issue(
        self, *, user: CurrentUser, public_id: str, content_locale: str
    ) -> PrescriptionRead:
        self._bind(user)
        row = await self._require(user, public_id)
        if row.status != "draft":
            raise PrescriptionInvalidStatusError(status=row.status)
        patient = await self._patient(user, int(row.patient_id))
        encounter_public_id = await self._encounter_public_id(user, row)
        encounter = await self._draft_encounter(user, encounter_public_id, patient)
        await self._load_chart(user, patient)
        prepared = await self._prepare_existing(user, patient, row)
        alerts = self._alerts_for(
            prepared, bool(row.is_pediatric), row.weight_kg_at_issue
        )
        self._refuse_blocks(prepared, alerts)
        now = datetime.now(UTC).replace(tzinfo=None)
        row.status = "issued"
        row.issued_at = now
        row.safety_alerts = _alert_payload(alerts)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._write_medications(user, patient, row, now)
        await self._session.flush()
        await get_event_bus().publish(
            prescription_event(
                PRESCRIPTION_ISSUED,
                prescription_public_id=row.public_id,
                clinic_id=user.clinic_id,
                patient_public_id=patient.public_id,
            )
        )
        loaded = await self._require(user, public_id)
        self._audit.record_access(
            action="issue",
            entity_type="prescription",
            clinic_id=user.clinic_id,
            entity_id=int(loaded.id),
            entity_public_id=loaded.public_id,
            patient_id=int(patient.id),
        )
        return await self._read(
            user, loaded, patient.public_id, encounter.public_id, content_locale
        )

    async def cancel(
        self, *, user: CurrentUser, public_id: str, content_locale: str
    ) -> PrescriptionRead:
        self._bind(user)
        row = await self._require(user, public_id)
        if row.status == "cancelled":
            raise PrescriptionInvalidStatusError(status=row.status)
        patient = await self._patient(user, int(row.patient_id))
        today = datetime.now(UTC).date()
        meds = await PatientMedicationRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_patient(int(patient.id), limit=SAFETY_CONTEXT_LIMIT)
        item_ids = {int(item.id) for item in row.items if item.deleted_at is None}
        for med in meds:
            if med.prescription_item_id is None:
                continue
            if int(med.prescription_item_id) not in item_ids:
                continue
            med.is_active = False
            med.stopped_on = today
            med.updated_by_id = user.user_id
        row.status = "cancelled"
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.flush()
        await get_event_bus().publish(
            prescription_event(
                PRESCRIPTION_CANCELLED,
                prescription_public_id=row.public_id,
                clinic_id=user.clinic_id,
                patient_public_id=patient.public_id,
            )
        )
        loaded = await self._require(user, public_id)
        return await self._read(
            user,
            loaded,
            patient.public_id,
            await self._encounter_public_id(user, loaded),
            content_locale,
        )

    async def get(
        self, *, user: CurrentUser, public_id: str, content_locale: str
    ) -> PrescriptionRead:
        self._bind(user)
        row = await self._require(user, public_id)
        patient = await self._patient(user, int(row.patient_id))
        alerts: list[dict[str, Any]] | None = None
        if row.status == "draft":
            await self._load_chart(user, patient)
            prepared = await self._prepare_existing(user, patient, row)
            alerts = _alert_payload(
                self._alerts_for(
                    prepared, bool(row.is_pediatric), row.weight_kg_at_issue
                )
            )
        self._audit.record_access(
            action="read",
            entity_type="prescription",
            clinic_id=user.clinic_id,
            entity_id=int(row.id),
            entity_public_id=row.public_id,
            patient_id=int(patient.id),
        )
        return await self._read(
            user,
            row,
            patient.public_id,
            await self._encounter_public_id(user, row),
            content_locale,
            alerts,
        )

    async def list_for_patient(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        page: PaginationParams,
        content_locale: str,
    ) -> PageSchema[PrescriptionRead]:
        self._bind(user)
        patient = await self._refs.patient(user, patient_public_id)
        found = await PrescriptionRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_patient(int(patient.id), page)
        items = [
            await self._read(
                user,
                row,
                patient.public_id,
                await self._encounter_public_id(user, row),
                content_locale,
            )
            for row in found.items
        ]
        return PageSchema(
            items=items,
            page=PageMeta(
                total=found.total,
                limit=found.limit,
                offset=found.offset,
                next_cursor=found.next_cursor,
            ),
        )

    async def check_safety(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        body: SafetyCheckRequest,
    ) -> list[SafetyAlertRead]:
        self._bind(user)
        patient = await self._refs.patient(user, patient_public_id)
        await self._load_chart(user, patient)
        prepared = await self._prepare(
            user, patient, body.items, body.weight_kg, body.is_pediatric
        )
        return [
            SafetyAlertRead(
                code=alert.code, severity=alert.severity, item_index=alert.item_index
            )
            for alert in self._alerts_for(prepared, body.is_pediatric, body.weight_kg)
        ]

    async def calculate_dose(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        body: PediatricDoseRequest,
    ) -> CalculationRead:
        self._bind(user)
        patient = await self._refs.patient(user, patient_public_id)
        entry = await self._formulary(user, body.formulary_entry_public_id)
        parsed = self._parsed(entry, body.indication_code)
        try:
            result = weight_based_dose(
                PediatricDoseInput(
                    weight_kg=body.weight_kg,
                    rule=self._rule(parsed),
                    concentration_mg_per_ml=entry.drug_form.concentration_mg_per_ml,
                    completed_years=self._years(patient),
                    age_caps=parsed.age_caps,
                )
            )
        except EngineInputError as exc:
            raise PrescriptionDosingInputError(reason=exc.code) from exc
        return calculation_read(result)

    async def generate_taper(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        body: TaperRequest,
    ) -> CalculationRead:
        self._bind(user)
        await self._refs.patient(user, patient_public_id)
        try:
            result = generate_steroid_taper(
                TaperInput(
                    start_mg=body.start_mg,
                    step_mg=body.step_mg,
                    days_per_step=body.days_per_step,
                    minimum_mg=body.minimum_mg,
                )
            )
        except EngineInputError as exc:
            raise PrescriptionDosingInputError(reason=exc.code) from exc
        return calculation_read(result.calculation)

    async def search_drugs(
        self,
        *,
        user: CurrentUser,
        q: str | None,
        page: PaginationParams,
        content_locale: str,
    ) -> PageSchema[DrugRead]:
        self._bind(user)
        found = await DrugRepository(self._session, clinic_id=None).search(q, page)
        labels = await self._labels(
            user,
            {
                int(drug.concept_id)
                for drug in found.items
                if drug.concept_id is not None
            },
            content_locale,
        )
        return PageSchema(
            items=[drug_read(row, labels) for row in found.items],
            page=PageMeta(
                total=found.total,
                limit=found.limit,
                offset=found.offset,
                next_cursor=found.next_cursor,
            ),
        )

    async def list_formulary(
        self,
        *,
        user: CurrentUser,
        q: str | None,
        page: PaginationParams,
        content_locale: str,
    ) -> PageSchema[FormularyEntryRead]:
        self._bind(user)
        found = await FormularyRepository(
            self._session, clinic_id=user.clinic_id
        ).list_available(page, q=q)
        labels = await self._labels(
            user, _formulary_concepts(found.items), content_locale
        )
        return PageSchema(
            items=[formulary_read(row, labels) for row in found.items],
            page=PageMeta(
                total=found.total,
                limit=found.limit,
                offset=found.offset,
                next_cursor=found.next_cursor,
            ),
        )

    async def create_formulary(
        self,
        *,
        user: CurrentUser,
        body: FormularyEntryCreate,
        content_locale: str,
    ) -> FormularyEntryRead:
        self._bind(user)
        form = await DrugFormRepository(self._session, clinic_id=None).get_loaded(
            body.drug_form_public_id
        )
        if form is None:
            raise NotFoundError(resource="drug_form", publicId=body.drug_form_public_id)
        document = None
        if body.dosing_rules is not None:
            document = dosing_rules_document(body.dosing_rules)
            self._parsed_document(document, None)
        row = FormularyEntry(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            drug_form_id=int(form.id),
            brand_name=body.brand_name,
            is_available=body.is_available,
            local_code=body.local_code,
            price=body.price,
            currency_code=body.currency_code,
            notes=body.notes,
            dosing_rules=document,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await FormularyRepository(self._session, clinic_id=user.clinic_id).add(row)
        loaded = await self._formulary(user, row.public_id)
        return formulary_read(
            loaded, await self._entry_labels(user, loaded, content_locale)
        )

    async def update_formulary(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: FormularyEntryUpdate,
        content_locale: str,
    ) -> FormularyEntryRead:
        self._bind(user)
        row = await self._formulary_row(user, public_id)
        if int(row.version) != body.version:
            raise PrescriptionVersionConflictError(
                server_version=int(row.version), client_version=body.version
            )
        if body.brand_name is not None:
            row.brand_name = body.brand_name
        if body.is_available is not None:
            row.is_available = body.is_available
        if body.local_code is not None:
            row.local_code = body.local_code
        if body.price is not None:
            row.price = body.price
        if body.currency_code is not None:
            row.currency_code = body.currency_code.upper()
        if body.notes is not None:
            row.notes = body.notes
        if body.dosing_rules is not None:
            document = dosing_rules_document(body.dosing_rules)
            self._parsed_document(document, None)
            row.dosing_rules = document
        if row.price is not None and row.currency_code is None:
            raise ValidationError(reason="currency_required")
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.flush()
        loaded = await self._formulary_row(user, public_id)
        return formulary_read(
            loaded, await self._entry_labels(user, loaded, content_locale)
        )

    async def list_templates(
        self, *, user: CurrentUser, page: PaginationParams
    ) -> PageSchema[PrescriptionTemplateRead]:
        self._bind(user)
        found = await PrescriptionTemplateRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_clinic(page)
        return PageSchema(
            items=[template_read(row) for row in found.items],
            page=PageMeta(
                total=found.total,
                limit=found.limit,
                offset=found.offset,
                next_cursor=found.next_cursor,
            ),
        )

    async def create_template(
        self, *, user: CurrentUser, body: PrescriptionTemplateCreate
    ) -> PrescriptionTemplateRead:
        self._bind(user)
        row = PrescriptionTemplate(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            user_id=user.user_id,
            code=body.code,
            name_key=body.name_key,
            complaint_concept_ids=list(body.complaint_concept_ids),
            items=[item.model_dump(mode="json", by_alias=True) for item in body.items],
            is_pediatric=body.is_pediatric,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await PrescriptionTemplateRepository(
            self._session, clinic_id=user.clinic_id
        ).add(row)
        return template_read(row)

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    async def _patient(self, user: CurrentUser, patient_id: int) -> Patient:
        row = await PatientRepository(self._session, clinic_id=user.clinic_id).get(
            patient_id
        )
        if row is None:
            raise NotFoundError(resource="patient")
        return row

    async def _draft_encounter(
        self, user: CurrentUser, public_id: str, patient: Patient
    ) -> Encounter:
        row = await EncounterRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_public_id(public_id)
        if row is None or int(row.patient_id) != int(patient.id):
            raise EncounterNotFoundError(resource="encounter", publicId=public_id)
        EncounterRepository(self._session, clinic_id=user.clinic_id).assert_draft(row)
        return row

    async def _encounter_public_id(self, user: CurrentUser, row: Prescription) -> str:
        encounter = await EncounterRepository(
            self._session, clinic_id=user.clinic_id
        ).get(int(row.encounter_id))
        if encounter is None:
            raise EncounterNotFoundError(resource="encounter")
        return str(encounter.public_id)

    async def _formulary_row(self, user: CurrentUser, public_id: str) -> FormularyEntry:
        row = await FormularyRepository(
            self._session, clinic_id=user.clinic_id
        ).get_loaded(public_id)
        if row is None:
            raise FormularyEntryNotFoundError(
                resource="formulary_entry", publicId=public_id
            )
        return row

    async def _formulary(self, user: CurrentUser, public_id: str) -> FormularyEntry:
        row = await self._formulary_row(user, public_id)
        if not row.is_available:
            raise FormularyEntryNotFoundError(
                resource="formulary_entry", publicId=public_id
            )
        return row

    async def _require(self, user: CurrentUser, public_id: str) -> Prescription:
        row = await PrescriptionRepository(
            self._session, clinic_id=user.clinic_id
        ).get_loaded(public_id)
        if row is None:
            raise PrescriptionNotFoundError(resource="prescription", publicId=public_id)
        return row

    def _parsed(self, entry: FormularyEntry, indication: str | None) -> ParsedDosing:
        document = entry.dosing_rules if isinstance(entry.dosing_rules, dict) else None
        return self._parsed_document(document, indication)

    def _parsed_document(
        self, document: dict[str, Any] | None, indication: str | None
    ) -> ParsedDosing:
        try:
            return parse_dosing_document(document, indication_code=indication)
        except DosingDocumentError as exc:
            raise PrescriptionDosingRuleError(reason=exc.code) from exc

    def _rule(self, parsed: ParsedDosing) -> DosingRule:
        try:
            return as_dosing_rule(parsed)
        except DosingDocumentError as exc:
            raise PrescriptionDosingRuleError(reason=exc.code) from exc

    def _years(self, patient: Patient) -> int:
        years, _months = completed_age(patient.birth_date, datetime.now(UTC).date())
        return years

    async def _prepare(
        self,
        user: CurrentUser,
        patient: Patient,
        items: list[PrescriptionItemWrite],
        weight: Decimal | None,
        is_pediatric: bool,
    ) -> list[_Prepared]:
        prepared: list[_Prepared] = []
        years = self._years(patient)
        for item in items:
            entry: FormularyEntry | None = None
            parsed: ParsedDosing | None = None
            if item.formulary_entry_public_id is not None:
                entry = await self._formulary(user, item.formulary_entry_public_id)
                if entry.dosing_rules is not None or item.calculate_from_formulary:
                    parsed = self._parsed(entry, item.indication_code)
            drug = None if entry is None else entry.drug_form.drug
            weight_based = bool(is_pediatric) or (
                parsed is not None and parsed.mg_per_kg_per_day is not None
            )
            dose_amount = item.dose_amount
            dose_unit = item.dose_unit
            volume: Decimal | None = None
            dosing: CalculationResult | None = None
            if item.calculate_from_formulary:
                weight_based = True
                if weight is not None and parsed is not None and entry is not None:
                    try:
                        dosing = weight_based_dose(
                            PediatricDoseInput(
                                weight_kg=weight,
                                rule=self._rule(parsed),
                                concentration_mg_per_ml=(
                                    entry.drug_form.concentration_mg_per_ml
                                ),
                                completed_years=years,
                                age_caps=parsed.age_caps,
                            )
                        )
                    except EngineInputError as exc:
                        raise PrescriptionDosingInputError(reason=exc.code) from exc
                    dose_amount = Decimal(dosing.value)
                    dose_unit = "mg"
                    volume = _volume(dosing)
            taper_days, taper_result = self._taper_for(item, parsed)
            concept_ids: frozenset[str] = frozenset()
            if drug is not None and drug.concept is not None:
                concept_ids = frozenset({str(drug.concept.public_id)})
            prepared.append(
                _Prepared(
                    body=item,
                    formulary=entry,
                    dose_amount=dose_amount,
                    dose_unit=dose_unit,
                    volume_ml=volume,
                    taper=taper_days,
                    dosing=dosing,
                    taper_result=taper_result,
                    weight_based=weight_based,
                    allergy_ids=concept_ids,
                    drug_class=None if drug is None else drug.drug_class,
                    is_ototoxic=bool(drug.is_ototoxic) if drug is not None else False,
                    pregnancy_category=(
                        None if drug is None else drug.pregnancy_category
                    ),
                    max_daily_mg=self._maximum(parsed, years),
                )
            )
        return prepared

    def _taper_for(
        self, item: PrescriptionItemWrite, parsed: ParsedDosing | None
    ) -> tuple[tuple[TaperDay, ...] | None, CalculationResult | None]:
        spec: TaperInput | None = None
        if item.taper is not None:
            spec = TaperInput(
                start_mg=item.taper.start_mg,
                step_mg=item.taper.step_mg,
                days_per_step=item.taper.days_per_step,
                minimum_mg=item.taper.minimum_mg,
            )
        elif item.use_formulary_taper:
            if parsed is None or parsed.taper is None:
                raise PrescriptionDosingRuleError(
                    reason="prescription.dosing_rule_invalid"
                )
            spec = parsed.taper
        if spec is None:
            return None, None
        try:
            result = generate_steroid_taper(spec)
        except EngineInputError as exc:
            raise PrescriptionDosingInputError(reason=exc.code) from exc
        return result.days, result.calculation

    def _maximum(self, parsed: ParsedDosing | None, years: int) -> Decimal | None:
        if parsed is None or (parsed.max_mg_per_day is None and not parsed.age_caps):
            return None
        try:
            return applicable_max_mg_per_day(
                PediatricDoseInput(
                    weight_kg=Decimal("1"),
                    rule=DosingRule(
                        mg_per_kg_per_day=parsed.mg_per_kg_per_day or Decimal("1"),
                        doses_per_day=parsed.doses_per_day or 1,
                        max_mg_per_day=parsed.max_mg_per_day,
                    ),
                    completed_years=years,
                    age_caps=parsed.age_caps,
                )
            )
        except EngineInputError as exc:
            raise PrescriptionDosingInputError(reason=exc.code) from exc

    async def _prepare_existing(
        self, user: CurrentUser, patient: Patient, row: Prescription
    ) -> list[_Prepared]:
        items: list[PrescriptionItemWrite] = []
        for item in row.items:
            if item.deleted_at is not None:
                continue
            formulary_id = None
            if item.drug_form_id is not None:
                entry = await self._formulary_for_form(user, int(item.drug_form_id))
                formulary_id = None if entry is None else entry.public_id
            items.append(
                PrescriptionItemWrite(
                    formulary_entry_public_id=formulary_id,
                    free_text_name=item.free_text_name,
                    dose_amount=item.dose_amount,
                    dose_unit=item.dose_unit,
                    route=item.route,  # type: ignore[arg-type]
                    frequency_per_day=int(item.frequency_per_day),
                    interval_hours=(
                        None
                        if item.interval_hours is None
                        else int(item.interval_hours)
                    ),
                    duration_days=int(item.duration_days),
                    quantity=item.quantity,
                    instructions_text=item.instructions_text,
                    is_renewable=bool(item.is_renewable),
                    substitution_allowed=bool(item.substitution_allowed),
                    sort_order=int(item.sort_order),
                    safety_overrides=_stored_overrides(item),
                )
            )
        return await self._prepare(
            user,
            patient,
            items,
            row.weight_kg_at_issue,
            bool(row.is_pediatric),
        )

    async def _formulary_for_form(
        self, user: CurrentUser, drug_form_id: int
    ) -> FormularyEntry | None:
        repo = FormularyRepository(self._session, clinic_id=user.clinic_id)
        found = await self._session.scalars(
            repo._base_query().where(FormularyEntry.drug_form_id == drug_form_id)
        )
        row = found.first()
        if row is None:
            return None
        return await repo.get_loaded(str(row.public_id))

    async def _load_chart(self, user: CurrentUser, patient: Patient) -> None:
        clinic = user.clinic_id
        patient_id = int(patient.id)
        allergies = await PatientAllergyRepository(
            self._session, clinic_id=clinic
        ).list_for_patient(patient_id, limit=SAFETY_CONTEXT_LIMIT)
        flags = await PatientFlagRepository(
            self._session, clinic_id=clinic
        ).list_for_patient(patient_id, limit=SAFETY_CONTEXT_LIMIT)
        problems = await PatientProblemRepository(
            self._session, clinic_id=clinic
        ).list_for_patient(patient_id, limit=SAFETY_CONTEXT_LIMIT)
        medications = await PatientMedicationRepository(
            self._session, clinic_id=clinic
        ).list_for_patient(patient_id, limit=SAFETY_CONTEXT_LIMIT)
        concept_ids = {
            int(row.substance_concept_id) for row in allergies if row.is_active
        }
        concept_ids.update(
            int(row.diagnosis_concept_id)
            for row in problems
            if row.status in {"active", "suspected"}
        )
        labels = await self._labels(user, concept_ids, "en")
        self._allergy_ids = frozenset(
            labels[int(row.substance_concept_id)][0]
            for row in allergies
            if row.is_active and int(row.substance_concept_id) in labels
        )
        self._hearing_loss = any(
            labels[int(row.diagnosis_concept_id)][1].startswith(
                HEARING_LOSS_CODE_PREFIXES
            )
            for row in problems
            if row.status in {"active", "suspected"}
            and int(row.diagnosis_concept_id) in labels
        )
        self._pregnant = any(
            row.flag_code == "pregnancy" and row.ended_on is None for row in flags
        )
        self._breastfeeding = any(
            row.flag_code == "breastfeeding" and row.ended_on is None for row in flags
        )
        drugs = await DrugRepository(self._session, clinic_id=None).get_by_ids(
            {
                int(row.drug_id)
                for row in medications
                if row.is_active and row.drug_id is not None
            }
        )
        self._classes = frozenset(drug.drug_class for drug in drugs if drug.drug_class)

    def _alerts_for(
        self,
        prepared: list[_Prepared],
        is_pediatric: bool,
        weight: Decimal | None,
    ) -> tuple[SafetyAlert, ...]:
        safety_items: list[SafetyItem] = []
        for item in prepared:
            daily = None
            if item.dose_amount is not None and item.dose_unit == "mg":
                daily = item.dose_amount * Decimal(item.body.frequency_per_day)
            safety_items.append(
                SafetyItem(
                    allergy_concept_ids=item.allergy_ids,
                    drug_class=item.drug_class,
                    is_ototoxic=item.is_ototoxic,
                    pregnancy_category=item.pregnancy_category,
                    daily_dose_mg=daily,
                    max_daily_dose_mg=item.max_daily_mg,
                    is_unstructured=item.formulary is None,
                )
            )
        return check_safety(
            SafetyInput(
                items=tuple(safety_items),
                active_allergy_concept_ids=self._allergy_ids,
                active_medication_classes=self._classes,
                hearing_loss_on_problem_list=self._hearing_loss,
                is_pregnant=self._pregnant,
                is_breastfeeding=self._breastfeeding,
                is_pediatric=is_pediatric
                or any(item.weight_based for item in prepared),
                weight_kg=weight,
            )
        )

    def _refuse_blocks(
        self, prepared: list[_Prepared], alerts: tuple[SafetyAlert, ...]
    ) -> None:
        covered = {
            (index, override.code)
            for index, item in enumerate(prepared)
            for override in item.body.safety_overrides
            if override.code in OVERRIDABLE_ALERTS
        }
        blocking = [
            alert
            for alert in alerts
            if alert.severity == "block"
            and (alert.item_index, alert.code) not in covered
        ]
        if blocking:
            raise PrescriptionBlockedError(alerts=_alert_payload(tuple(blocking)))

    async def _insert(
        self,
        user: CurrentUser,
        patient: Patient,
        encounter: Encounter,
        body: PrescriptionCreate,
        prepared: list[_Prepared],
        alerts: tuple[SafetyAlert, ...],
    ) -> Prescription:
        row = Prescription(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            encounter_id=int(encounter.id),
            prescriber_id=user.user_id,
            locale=body.locale,
            status="draft",
            notes=body.notes,
            weight_kg_at_issue=body.weight_kg,
            is_pediatric=body.is_pediatric
            or any(item.weight_based for item in prepared),
            safety_alerts=_alert_payload(alerts),
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await PrescriptionRepository(self._session, clinic_id=user.clinic_id).add(row)
        await self._add_items(user, patient, encounter, row, prepared)
        return row

    async def _add_items(
        self,
        user: CurrentUser,
        patient: Patient,
        encounter: Encounter,
        row: Prescription,
        prepared: list[_Prepared],
    ) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)
        for item in prepared:
            stored = PrescriptionItem(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                prescription_id=int(row.id),
                drug_form_id=(
                    None if item.formulary is None else int(item.formulary.drug_form_id)
                ),
                free_text_name=item.body.free_text_name,
                dose_amount=item.dose_amount,
                dose_unit=item.dose_unit,
                volume_ml=item.volume_ml,
                route=item.body.route,
                frequency_per_day=item.body.frequency_per_day,
                interval_hours=item.body.interval_hours,
                duration_days=item.body.duration_days,
                quantity=item.body.quantity,
                instructions_text=item.body.instructions_text,
                taper_schedule=_taper_payload(item.taper),
                is_renewable=item.body.is_renewable,
                substitution_allowed=item.body.substitution_allowed,
                safety_overrides=_override_payload(item, user, now),
                sort_order=item.body.sort_order,
                dosing_engine_version=(
                    None if item.dosing is None else item.dosing.version
                ),
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
            self._session.add(stored)
            await self._session.flush()
            for result in (item.dosing, item.taper_result):
                if result is None:
                    continue
                await CalculationResultRepository(
                    self._session, clinic_id=user.clinic_id
                ).add(_calculation_row(user, patient, encounter, result, now))

    async def _replace_items(
        self, user: CurrentUser, row: Prescription, prepared: list[_Prepared]
    ) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)
        for item in list(row.items):
            if item.deleted_at is None:
                item.deleted_at = now
                item.deleted_by_id = user.user_id
        patient = await self._patient(user, int(row.patient_id))
        encounter = await EncounterRepository(
            self._session, clinic_id=user.clinic_id
        ).get(int(row.encounter_id))
        if encounter is None:
            raise EncounterNotFoundError(resource="encounter")
        await self._add_items(user, patient, encounter, row, prepared)

    async def _write_medications(
        self, user: CurrentUser, patient: Patient, row: Prescription, now: datetime
    ) -> None:
        for item in row.items:
            if item.deleted_at is not None or item.dose_amount is None:
                continue
            drug_id = None
            ototoxic = False
            anticoagulant = False
            name = item.free_text_name
            if item.drug_form is not None:
                drug_id = int(item.drug_form.drug_id)
                ototoxic = bool(item.drug_form.drug.is_ototoxic)
                anticoagulant = bool(item.drug_form.drug.is_anticoagulant)
                name = name or item.drug_form.drug.inn_name
            await PatientMedicationRepository(
                self._session, clinic_id=user.clinic_id
            ).add(
                PatientMedication(
                    public_id=new_ulid(),
                    clinic_id=user.clinic_id,
                    patient_id=int(patient.id),
                    drug_id=drug_id,
                    free_text_name=name,
                    dose=f"{item.dose_amount} {item.dose_unit or ''}".strip(),
                    frequency=str(item.frequency_per_day),
                    route=item.route,
                    started_on=now.date(),
                    is_active=True,
                    is_anticoagulant=anticoagulant,
                    is_ototoxic=ototoxic,
                    source="prescribed_here",
                    prescription_item_id=int(item.id),
                    created_by_id=user.user_id,
                    updated_by_id=user.user_id,
                )
            )

    async def _read(
        self,
        user: CurrentUser,
        row: Prescription,
        patient_public_id: str,
        encounter_public_id: str,
        content_locale: str,
        alerts: list[dict[str, Any]] | None = None,
    ) -> PrescriptionRead:
        concept_ids = {
            int(item.drug_form.drug.concept_id)
            for item in row.items
            if item.drug_form is not None and item.drug_form.drug.concept_id is not None
        }
        return prescription_read(
            row,
            patient_public_id=patient_public_id,
            encounter_public_id=encounter_public_id,
            labels=await self._labels(user, concept_ids, content_locale),
            alerts=alerts,
        )

    async def _labels(
        self, user: CurrentUser, concept_ids: set[int], content_locale: str
    ) -> dict[int, tuple[str, str, str | None]]:
        if not concept_ids:
            return {}
        return await self._refs.labels(user, concept_ids, content_locale)

    async def _entry_labels(
        self, user: CurrentUser, row: FormularyEntry, content_locale: str
    ) -> dict[int, tuple[str, str, str | None]]:
        concept_id = row.drug_form.drug.concept_id
        if concept_id is None:
            return {}
        return await self._labels(user, {int(concept_id)}, content_locale)

    async def _replay(
        self, user: CurrentUser, key: str | None, body: PrescriptionCreate
    ) -> str | None:
        if not key:
            return None
        existing = await PrescriptionIdempotencyRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_key(key)
        if existing is None:
            return None
        if existing.request_hash != _hash(body) or existing.resource_type != _CREATE:
            raise PrescriptionIdempotencyMismatchError()
        return existing.resource_public_id

    async def _store_idempotency(
        self,
        user: CurrentUser,
        key: str | None,
        body: PrescriptionCreate,
        resource_public_id: str,
    ) -> None:
        if not key:
            return
        await PrescriptionIdempotencyRepository(
            self._session, clinic_id=user.clinic_id
        ).add(
            PrescriptionRequestIdempotency(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                idempotency_key=key,
                request_hash=_hash(body),
                resource_type=_CREATE,
                resource_public_id=resource_public_id,
            )
        )


def _hash(body: PrescriptionCreate) -> str:
    raw = json.dumps(
        body.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _volume(result: CalculationResult) -> Decimal | None:
    for flag in result.flags:
        if flag.code == "volume_ml":
            return Decimal(flag.detail["value"])
    return None


def _alert_payload(alerts: tuple[SafetyAlert, ...]) -> list[dict[str, Any]]:
    return [
        {
            "code": alert.code,
            "severity": alert.severity,
            "item_index": alert.item_index,
        }
        for alert in alerts
    ]


def _override_payload(
    item: _Prepared, user: CurrentUser, now: datetime
) -> list[dict[str, str]]:
    return [
        {
            "code": override.code,
            "reason": override.reason,
            "user_public_id": user.user_public_id,
            "at": now.isoformat(),
        }
        for override in item.body.safety_overrides
    ]


def _stored_overrides(item: PrescriptionItem) -> list[SafetyOverrideWrite]:
    raw = item.safety_overrides if isinstance(item.safety_overrides, list) else []
    overrides: list[SafetyOverrideWrite] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        code = entry.get("code")
        reason = entry.get("reason")
        if (
            not isinstance(code, str)
            or code not in OVERRIDABLE_ALERTS
            or not isinstance(reason, str)
            or not reason
        ):
            continue
        overrides.append(
            SafetyOverrideWrite(code=cast(OverrideCode, code), reason=reason)
        )
    return overrides


def _taper_payload(
    days: tuple[TaperDay, ...] | None,
) -> list[dict[str, object]] | None:
    if days is None:
        return None
    return [{"day": day.day_number, "doseMg": format(day.dose_mg, "f")} for day in days]


def _calculation_row(
    user: CurrentUser,
    patient: Patient,
    encounter: Encounter,
    result: CalculationResult,
    now: datetime,
) -> CalculationResultRow:
    return CalculationResultRow(
        public_id=new_ulid(),
        clinic_id=user.clinic_id,
        patient_id=int(patient.id),
        encounter_id=int(encounter.id),
        calculator_code=result.code,
        engine_version=result.version,
        inputs=dict(result.inputs),
        value=result.value,
        unit=result.unit,
        flags=[
            {"code": flag.code, "detail": dict(flag.detail)} for flag in result.flags
        ],
        reference=result.reference[:255],
        computed_at=now,
        computed_by_id=user.user_id,
        created_by_id=user.user_id,
        updated_by_id=user.user_id,
    )


def _formulary_concepts(rows: list[FormularyEntry]) -> set[int]:
    return {
        int(row.drug_form.drug.concept_id)
        for row in rows
        if row.drug_form.drug.concept_id is not None
    }
