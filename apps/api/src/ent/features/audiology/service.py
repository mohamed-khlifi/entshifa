"""Audiogram use cases (P4-01 entry, P4-02 calculations)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import ValidationError
from ent.core.events.bus import get_event_bus
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.engines.audiology.types import AsymmetryRule, PtaFormula, ShiftRule
from ent.features.audiology.events import (
    _CREATE_RESOURCE,
    audiogram_baseline_changed_event,
    audiogram_created_event,
)
from ent.features.audiology.exceptions import (
    AudiogramDuplicateThresholdError,
    AudiogramIdempotencyMismatchError,
    AudiogramIncompleteThresholdsError,
    AudiogramLockedError,
    AudiogramNotFoundError,
    AudiogramVersionConflictError,
)
from ent.features.audiology.mapping import audiogram_read, to_page
from ent.features.audiology.models import Audiogram, AudiologyRequestIdempotency
from ent.features.audiology.policies import assert_interpret_fields
from ent.features.audiology.references import AudiologyReferences
from ent.features.audiology.repository import (
    AudiogramRepository,
    AudiologyIdempotencyRepository,
)
from ent.features.audiology.schemas.requests import (
    AudiogramBaselineUpdate,
    AudiogramCreate,
    AudiogramInterpret,
    AudiogramUpdate,
    ThresholdInput,
)
from ent.features.audiology.schemas.responses import AudiogramRead
from ent.features.audiology.scoring import (
    apply_metrics_to_audiogram,
    compute_metrics,
    metric_rows_for_audiogram,
    threshold_points_from_rows,
)
from ent.features.clinics.resolver import SettingResolver
from ent.features.clinics.setting_keys import (
    AsymmetryRuleValue,
    ClinicalSettingKey,
    ShiftRuleValue,
)
from ent.features.encounters.repository import EncounterRepository
from ent.features.procedures.mapping import blank_to_none, to_utc_naive


class AudiologyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = AudiologyReferences(session)

    async def create_audiogram(
        self,
        *,
        user: CurrentUser,
        body: AudiogramCreate,
        idempotency_key: str | None,
    ) -> AudiogramRead:
        self._bind(user)
        replay = await self._replay(user, idempotency_key, body)
        if replay is not None:
            return await self.get_audiogram(user=user, public_id=replay)
        assert_interpret_fields(
            user,
            interpretation_text=body.interpretation_text,
            is_baseline=body.is_baseline,
        )
        _assert_unique_thresholds(body.thresholds)
        patient = await self._refs.patient(user, body.patient_public_id)
        baseline = await self._refs.baseline_audiogram(
            user,
            body.baseline_audiogram_public_id,
            patient_id=int(patient.id),
        )
        performed_at = body.performed_at or datetime.now(UTC).replace(tzinfo=None)
        performer_public_id = body.performed_by_public_id or user.user_public_id
        row = Audiogram(
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            encounter_id=await self._refs.encounter_id(
                user,
                body.encounter_public_id,
                patient_id=int(patient.id),
            ),
            performed_at=to_utc_naive(performed_at),
            performed_by_id=await self._refs.member_id(user, performer_public_id),
            equipment=blank_to_none(body.equipment),
            calibration_date=body.calibration_date,
            transducer=body.transducer,
            method=body.method,
            reliability=body.reliability,
            is_baseline=body.is_baseline,
            baseline_audiogram_id=int(baseline.id) if baseline is not None else None,
            interpretation_text=blank_to_none(body.interpretation_text),
            status="draft",
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await self._audiograms(user).add(row)
        await self._session.flush()
        if body.thresholds:
            await self._audiograms(user).sync_thresholds(
                row, body.thresholds, user_id=user.user_id
            )
            await self._session.flush()
            await self._session.refresh(row)
            await self._recompute_metrics(user, row)
        if body.is_baseline:
            await self._audiograms(user).clear_other_baselines(
                patient_id=int(patient.id),
                keep_audiogram_id=int(row.id),
            )
        await self._store_idempotency(user, idempotency_key, body, row.public_id)
        await self._session.commit()
        return await self.get_audiogram(user=user, public_id=row.public_id)

    async def get_audiogram(
        self,
        *,
        user: CurrentUser,
        public_id: str,
    ) -> AudiogramRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._audit.record_access(
            action="get",
            entity_type="audiogram",
            clinic_id=user.clinic_id,
            entity_id=int(row.id),
            entity_public_id=row.public_id,
            patient_id=int(row.patient_id),
        )
        await self._session.commit()
        await self._session.refresh(row)
        return audiogram_read(row)

    async def list_audiograms(
        self,
        *,
        user: CurrentUser,
        page: PaginationParams,
        patient_public_id: str | None = None,
        encounter_public_id: str | None = None,
    ) -> PageSchema[AudiogramRead]:
        self._bind(user)
        patient_id = None
        encounter_id = None
        if patient_public_id is not None:
            patient_id = int((await self._refs.patient(user, patient_public_id)).id)
        if encounter_public_id is not None:
            encounter = await EncounterRepository(
                self._session, clinic_id=user.clinic_id
            ).get_by_public_id(encounter_public_id)
            if encounter is None:
                raise ValidationError(reason="encounter_not_found")
            encounter_id = int(encounter.id)
            if patient_id is None:
                patient_id = int(encounter.patient_id)
            elif patient_id != int(encounter.patient_id):
                raise ValidationError(reason="encounter_patient")
        result = await self._audiograms(user).list_audiograms(
            page,
            patient_id=patient_id,
            encounter_id=encounter_id,
        )
        items = [audiogram_read(row) for row in result.items]
        self._audit.record_access(
            action="list",
            entity_type="audiogram",
            clinic_id=user.clinic_id,
            patient_id=patient_id,
        )
        await self._session.commit()
        return to_page(
            items,
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    async def update_audiogram(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: AudiogramUpdate,
    ) -> AudiogramRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._check_version(row, body.version)
        if row.status == "final":
            raise AudiogramLockedError(public_id=public_id)
        data = body.model_dump(exclude_unset=True)
        assert_interpret_fields(
            user,
            interpretation_text=data.get("interpretation_text"),
            is_baseline=data.get("is_baseline"),
        )
        if body.thresholds is not None:
            _assert_unique_thresholds(body.thresholds)
        await self._apply_update(user, row, body)
        if body.thresholds is not None:
            await self._session.flush()
            await self._session.refresh(row)
            await self._recompute_metrics(user, row)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.commit()
        return await self.get_audiogram(user=user, public_id=row.public_id)

    async def finalize_audiogram(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        version: int,
    ) -> AudiogramRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._check_version(row, version)
        if row.status == "final":
            raise AudiogramLockedError(public_id=public_id)
        if not row.thresholds:
            raise AudiogramIncompleteThresholdsError()
        await self._recompute_metrics(user, row, require_complete=False)
        row.status = "final"
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.commit()
        encounter_public_id = row.encounter.public_id if row.encounter else None
        await get_event_bus().publish(
            audiogram_created_event(
                clinic_id=user.clinic_id,
                audiogram_public_id=row.public_id,
                patient_public_id=row.patient.public_id,
                encounter_public_id=encounter_public_id,
            )
        )
        return await self.get_audiogram(user=user, public_id=row.public_id)

    async def interpret_audiogram(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: AudiogramInterpret,
    ) -> AudiogramRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._check_version(row, body.version)
        assert_interpret_fields(
            user,
            interpretation_text=body.interpretation_text,
            is_baseline=body.is_baseline,
        )
        if body.interpretation_text is not None:
            row.interpretation_text = blank_to_none(body.interpretation_text)
        if body.is_baseline is not None:
            await self._set_baseline(user, row, is_baseline=body.is_baseline)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.commit()
        return await self.get_audiogram(user=user, public_id=row.public_id)

    async def update_baseline(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: AudiogramBaselineUpdate,
    ) -> AudiogramRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._check_version(row, body.version)
        assert_interpret_fields(
            user, interpretation_text=None, is_baseline=body.is_baseline
        )
        await self._set_baseline(user, row, is_baseline=body.is_baseline)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.commit()
        return await self.get_audiogram(user=user, public_id=row.public_id)

    async def _apply_update(
        self,
        user: CurrentUser,
        row: Audiogram,
        body: AudiogramUpdate,
    ) -> None:
        if body.encounter_public_id is not None:
            row.encounter_id = await self._refs.encounter_id(
                user,
                body.encounter_public_id,
                patient_id=int(row.patient_id),
            )
        if body.performed_at is not None:
            row.performed_at = to_utc_naive(body.performed_at)
        if body.performed_by_public_id is not None:
            row.performed_by_id = await self._refs.member_id(
                user, body.performed_by_public_id
            )
        if body.equipment is not None:
            row.equipment = blank_to_none(body.equipment)
        if body.calibration_date is not None:
            row.calibration_date = body.calibration_date
        if body.transducer is not None:
            row.transducer = body.transducer
        if body.method is not None:
            row.method = body.method
        if body.reliability is not None:
            row.reliability = body.reliability
        if body.baseline_audiogram_public_id is not None:
            baseline = await self._refs.baseline_audiogram(
                user,
                body.baseline_audiogram_public_id,
                patient_id=int(row.patient_id),
            )
            row.baseline_audiogram_id = int(baseline.id) if baseline else None
        if body.interpretation_text is not None:
            row.interpretation_text = blank_to_none(body.interpretation_text)
        if body.is_baseline is not None:
            await self._set_baseline(user, row, is_baseline=body.is_baseline)
        if body.thresholds is not None:
            await self._audiograms(user).sync_thresholds(
                row, body.thresholds, user_id=user.user_id
            )

    async def _recompute_metrics(
        self,
        user: CurrentUser,
        row: Audiogram,
        *,
        require_complete: bool = False,
    ) -> None:
        if not row.thresholds:
            return
        pta_formula, asymmetry_rule, shift_rule = await self._calc_settings(user)
        baseline_points = None
        if row.baseline_audiogram_id is not None:
            loaded = await self._audiograms(user).get_detail(row.public_id)
            if (
                loaded is not None
                and loaded.baseline_audiogram is not None
                and loaded.baseline_audiogram.thresholds
            ):
                baseline_points = threshold_points_from_rows(
                    list(loaded.baseline_audiogram.thresholds)
                )
        metrics = compute_metrics(
            thresholds=threshold_points_from_rows(list(row.thresholds)),
            pta_formula=pta_formula,
            asymmetry_rule=asymmetry_rule,
            shift_rule=shift_rule,
            baseline_thresholds=baseline_points,
            require_complete=require_complete,
        )
        apply_metrics_to_audiogram(row, metrics)
        await self._audiograms(user).replace_metrics(
            int(row.id),
            metric_rows_for_audiogram(
                audiogram=row,
                metrics=metrics,
                clinic_id=user.clinic_id,
                user_id=user.user_id,
            ),
            user_id=user.user_id,
        )

    async def _calc_settings(
        self, user: CurrentUser
    ) -> tuple[PtaFormula, AsymmetryRule, ShiftRule]:
        resolver = SettingResolver(self._session)
        pta_resolved = await resolver.resolve(
            key=ClinicalSettingKey.PTA_FORMULA.value,
            clinic_id=user.clinic_id,
            user_id=user.user_id,
        )
        asym_resolved = await resolver.resolve(
            key=ClinicalSettingKey.ASYMMETRY_RULE.value,
            clinic_id=user.clinic_id,
            user_id=user.user_id,
        )
        shift_resolved = await resolver.resolve(
            key=ClinicalSettingKey.SHIFT_RULE.value,
            clinic_id=user.clinic_id,
            user_id=user.user_id,
        )
        pta = pta_resolved.value
        if not isinstance(pta, str):
            raise ValidationError(reason="invalid_pta_formula")
        asym = AsymmetryRuleValue.model_validate(asym_resolved.value)
        shift = ShiftRuleValue.model_validate(shift_resolved.value)
        return (
            pta,  # type: ignore[return-value]
            AsymmetryRule(
                adjacent_db=asym.adjacent_db,
                adjacent_count=asym.adjacent_count,
                single_db=asym.single_db,
                wrs_percent=asym.wrs_percent,
            ),
            shift.rule,
        )

    async def _set_baseline(
        self,
        user: CurrentUser,
        row: Audiogram,
        *,
        is_baseline: bool,
    ) -> None:
        row.is_baseline = is_baseline
        if is_baseline:
            await self._audiograms(user).clear_other_baselines(
                patient_id=int(row.patient_id),
                keep_audiogram_id=int(row.id),
            )
            await get_event_bus().publish(
                audiogram_baseline_changed_event(
                    clinic_id=user.clinic_id,
                    audiogram_public_id=row.public_id,
                    patient_public_id=row.patient.public_id,
                    is_baseline=True,
                )
            )

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    def _audiograms(self, user: CurrentUser) -> AudiogramRepository:
        return AudiogramRepository(self._session, clinic_id=user.clinic_id)

    async def _require(self, user: CurrentUser, public_id: str) -> Audiogram:
        row = await self._audiograms(user).get_detail(public_id)
        if row is None:
            raise AudiogramNotFoundError(public_id=public_id)
        await self._refs.assert_patient_visible(user, int(row.patient_id))
        return row

    def _check_version(self, row: Audiogram, version: int) -> None:
        if int(row.version) != version:
            raise AudiogramVersionConflictError(
                server_version=int(row.version),
                client_version=version,
            )

    async def _replay(
        self, user: CurrentUser, key: str | None, body: AudiogramCreate
    ) -> str | None:
        if not key:
            return None
        existing = await AudiologyIdempotencyRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_key(key)
        if existing is None:
            return None
        if (
            existing.request_hash != _hash(body)
            or existing.resource_type != _CREATE_RESOURCE
        ):
            raise AudiogramIdempotencyMismatchError()
        return existing.resource_public_id

    async def _store_idempotency(
        self,
        user: CurrentUser,
        key: str | None,
        body: AudiogramCreate,
        resource_public_id: str,
    ) -> None:
        if not key:
            return
        await AudiologyIdempotencyRepository(
            self._session, clinic_id=user.clinic_id
        ).add(
            AudiologyRequestIdempotency(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                idempotency_key=key,
                request_hash=_hash(body),
                resource_type=_CREATE_RESOURCE,
                resource_public_id=resource_public_id,
            )
        )


def _hash(body: AudiogramCreate) -> str:
    raw = json.dumps(
        body.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _assert_unique_thresholds(thresholds: list[ThresholdInput]) -> None:
    seen: set[tuple[str, str, int, bool]] = set()
    for item in thresholds:
        key = (item.ear, item.conduction, item.frequency_hz, item.is_masked)
        if key in seen:
            raise AudiogramDuplicateThresholdError()
        seen.add(key)
