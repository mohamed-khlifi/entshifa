"""Device, flag, and recall side effects for an otology save.

Intervals are clinic settings. The protocol resolver in P3-08 replaces the
direct recall rows; these rows are the schedule the tube insertion must create.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.clinics.repository import ClinicRepository
from ent.features.clinics.resolver import SettingResolver
from ent.features.clinics.setting_keys import (
    ClinicalSettingKey,
    FollowUpDefaultsValue,
    OtologyFollowUpValue,
)
from ent.features.otology.constants import (
    CHOLESTEATOMA_CODE,
    CLOSED_DEVICE_STATUSES,
    FLAG_CAVITY,
    FLAG_CHOLESTEATOMA,
    FLAG_TUBE,
    REASON_CANAL_INJURY,
    REASON_CAVITY,
    REASON_TUBE_CHECK,
    REASON_TUBE_PATENCY,
    REASON_WICK,
    TUBE_REASON_KEYS,
)
from ent.features.otology.dates import FollowUpPlan, add_days, add_months
from ent.features.otology.exceptions import (
    EarDeviceNotFoundError,
    OtologyInvalidExamError,
)
from ent.features.otology.models import EarDevice, OfficeProcedure
from ent.features.otology.repository import (
    EarDeviceRepository,
    ProcedureRecallRepository,
)
from ent.features.otology.schemas.requests import (
    CavityCleaningWrite,
    ForeignBodyWrite,
    OtologyCreate,
    OtologyUpdate,
    TubeInsertionWrite,
    TubeRemovalWrite,
    WaxRemovalWrite,
    WickWrite,
)
from ent.features.patients.models import PatientFlag
from ent.features.patients.repository import PatientFlagRepository
from ent.features.procedures.models import ProcedureRecord
from ent.features.recalls.dates import clinic_local_date
from ent.features.recalls.models import Recall

Write = OtologyCreate | OtologyUpdate
_SUPERSEDED = "otology_superseded"


async def load_plan(session: AsyncSession, user: CurrentUser) -> FollowUpPlan:
    resolver = SettingResolver(session)
    tube = await resolver.resolve(
        key=ClinicalSettingKey.TUBE_RECALL_INTERVAL_MONTHS.value,
        clinic_id=user.clinic_id,
        user_id=user.user_id,
    )
    follow = await resolver.resolve(
        key=ClinicalSettingKey.OTOLOGY_FOLLOW_UP.value,
        clinic_id=user.clinic_id,
        user_id=user.user_id,
    )
    defaults = await resolver.resolve(
        key=ClinicalSettingKey.FOLLOW_UP_DEFAULTS.value,
        clinic_id=user.clinic_id,
        user_id=user.user_id,
    )
    months = tube.value
    if not isinstance(months, int) or isinstance(months, bool):
        raise ValidationError(reason="invalid_tube_recall_interval")
    plan = OtologyFollowUpValue.model_validate(follow.value)
    routine = FollowUpDefaultsValue.model_validate(defaults.value)
    return FollowUpPlan(
        tube_first_check_days=plan.tube_first_check_days,
        tube_first_window_days=plan.tube_first_window_days,
        tube_interval_months=months,
        tube_interval_window_days=plan.tube_interval_window_days,
        wick_removal_days=plan.wick_removal_days,
        wick_window_days=plan.wick_window_days,
        cavity_cleaning_months=plan.cavity_cleaning_months,
        cavity_window_days=plan.cavity_window_days,
        canal_injury_days=routine.post_op_days,
        canal_injury_window_days=plan.canal_injury_window_days,
    )


async def clinic_today(session: AsyncSession, user: CurrentUser) -> date:
    clinic = await ClinicRepository(session).get(user.clinic_id)
    if clinic is None:
        raise NotFoundError(resource="clinic")
    return clinic_local_date(datetime.now(UTC), clinic.timezone)


async def performed_on(
    session: AsyncSession,
    user: CurrentUser,
    procedure: ProcedureRecord,
) -> date:
    clinic = await ClinicRepository(session).get(user.clinic_id)
    if clinic is None:
        raise NotFoundError(resource="clinic")
    return clinic_local_date(procedure.performed_at, clinic.timezone)


async def reconcile(
    session: AsyncSession,
    user: CurrentUser,
    procedure: ProcedureRecord,
    office: OfficeProcedure | None,
    body: Write,
    plan: FollowUpPlan,
    on: date,
) -> None:
    """Align devices, card flags, and recalls with the saved procedure block."""

    devices = EarDeviceRepository(session, clinic_id=user.clinic_id)
    recalls = ProcedureRecallRepository(session, clinic_id=user.clinic_id)
    flags = PatientFlagRepository(session, clinic_id=user.clinic_id)
    owned = await devices.list_for_inserted_procedure(int(procedure.id))
    open_devices = await devices.list_open_for_patient(int(procedure.patient_id))
    active_flags = await flags.list_active(
        flag_code=None,
        patient_id=int(procedure.patient_id),
        limit=200,
    )
    block = body.procedure
    side = body.laterality.value
    keep_devices: list[EarDevice] = []
    recalls_wanted: list[tuple[str, date, int, str]] = []
    removal_due: date | None = None

    if isinstance(block, TubeInsertionWrite):
        device = _take_owned(owned, "ventilation_tube")
        if device is None:
            _reject_existing_tube(open_devices, side)
            device = _new_device(
                user,
                procedure,
                device_type="ventilation_tube",
                laterality=side,
                on=on,
                tube_model=block.tube_model,
                complication=block.complication,
                next_check_due=add_days(on, plan.tube_first_check_days),
            )
            await devices.add(device)
        else:
            device.laterality = side
            device.tube_model = block.tube_model
            device.complication = block.complication
            device.status = "in_place"
            device.removed_at = None
            device.next_check_due = add_days(on, plan.tube_first_check_days)
            device.updated_by_id = user.user_id
        keep_devices.append(device)
        recalls_wanted.append(
            (
                REASON_TUBE_PATENCY,
                add_days(on, plan.tube_first_check_days),
                plan.tube_first_window_days,
                side,
            )
        )
        recalls_wanted.append(
            (
                REASON_TUBE_CHECK,
                add_months(on, plan.tube_interval_months),
                plan.tube_interval_window_days,
                side,
            )
        )
    elif isinstance(block, TubeRemovalWrite):
        target = await devices.get_detail(block.device_public_id)
        if (
            target is None
            or int(target.patient_id) != int(procedure.patient_id)
            or target.device_type != "ventilation_tube"
        ):
            raise EarDeviceNotFoundError(public_id=block.device_public_id)
        if target.status not in CLOSED_DEVICE_STATUSES:
            target.status = "removed"
            target.removed_at = on
            target.updated_by_id = user.user_id
        end_matching_flags(active_flags, FLAG_TUBE, target.laterality, on, user.user_id)
        await cancel_tube_recalls(
            recalls, int(procedure.patient_id), target.laterality, user.user_id
        )
    elif isinstance(block, CavityCleaningWrite):
        device = _take_owned(owned, "mastoid_cavity") or _open_cavity(
            open_devices, side
        )
        due = add_months(on, plan.cavity_cleaning_months)
        if device is None:
            device = _new_device(
                user,
                procedure,
                device_type="mastoid_cavity",
                laterality=side,
                on=on,
                tube_model=None,
                complication=None,
                next_check_due=due,
            )
            await devices.add(device)
        else:
            device.next_check_due = due
            device.updated_by_id = user.user_id
        keep_devices.append(device)
        recalls_wanted.append((REASON_CAVITY, due, plan.cavity_window_days, side))
    elif isinstance(block, WickWrite):
        removal_due = add_days(on, plan.wick_removal_days)
        recalls_wanted.append((REASON_WICK, removal_due, plan.wick_window_days, side))
    elif isinstance(block, WaxRemovalWrite) and block.canal_condition == "traumatized":
        recalls_wanted.append(
            (
                REASON_CANAL_INJURY,
                add_days(on, plan.canal_injury_days),
                plan.canal_injury_window_days,
                side,
            )
        )
    elif isinstance(block, ForeignBodyWrite) and block.trauma != "none":
        recalls_wanted.append(
            (
                REASON_CANAL_INJURY,
                add_days(on, plan.canal_injury_days),
                plan.canal_injury_window_days,
                side,
            )
        )

    if office is not None:
        office.removal_due_date = removal_due
    _retire_owned(owned, keep_devices, user.user_id)
    await _replace_recalls(recalls, user, procedure, recalls_wanted)
    await _sync_flags(
        flags,
        user,
        procedure,
        active_flags,
        body,
        keep_devices,
        on,
    )


def _take_owned(owned: list[EarDevice], device_type: str) -> EarDevice | None:
    return next((row for row in owned if row.device_type == device_type), None)


def _open_cavity(rows: list[EarDevice], laterality: str) -> EarDevice | None:
    return next(
        (
            row
            for row in rows
            if row.device_type == "mastoid_cavity" and row.laterality == laterality
        ),
        None,
    )


def _reject_existing_tube(rows: list[EarDevice], laterality: str) -> None:
    if any(
        row.device_type == "ventilation_tube" and row.laterality == laterality
        for row in rows
    ):
        raise OtologyInvalidExamError(reason="tube_already_present")


def _new_device(
    user: CurrentUser,
    procedure: ProcedureRecord,
    *,
    device_type: str,
    laterality: str,
    on: date,
    tube_model: str | None,
    complication: str | None,
    next_check_due: date,
) -> EarDevice:
    return EarDevice(
        public_id=new_ulid(),
        clinic_id=user.clinic_id,
        patient_id=int(procedure.patient_id),
        laterality=laterality,
        device_type=device_type,
        inserted_at=on,
        inserted_procedure_id=int(procedure.id),
        tube_model=tube_model,
        status="in_place",
        complication=complication,
        next_check_due=next_check_due,
        created_by_id=user.user_id,
        updated_by_id=user.user_id,
    )


def _retire_owned(
    owned: list[EarDevice],
    keep: list[EarDevice],
    user_id: int,
) -> None:
    kept = {id(row) for row in keep}
    now = datetime.now(UTC).replace(tzinfo=None)
    for row in owned:
        if id(row) in kept or row.deleted_at is not None:
            continue
        row.deleted_at = now
        row.deleted_by_id = user_id
        row.updated_by_id = user_id


async def _replace_recalls(
    repo: ProcedureRecallRepository,
    user: CurrentUser,
    procedure: ProcedureRecord,
    wanted: list[tuple[str, date, int, str]],
) -> None:
    existing = await repo.list_for_procedure(int(procedure.id))
    for row in existing:
        if row.status in {"pending", "unreachable"}:
            row.status = "cancelled"
            row.cancelled_reason = _SUPERSEDED
            row.updated_by_id = user.user_id
    for reason_key, due_on, window_days, laterality in wanted:
        await repo.add(
            Recall(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                patient_id=int(procedure.patient_id),
                source_type="procedure",
                source_id=int(procedure.id),
                reason_key=reason_key,
                due_on=due_on,
                window_days=window_days,
                action_type="visit",
                action_config={"reasonKey": reason_key},
                laterality=laterality,
                status="pending",
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
        )


async def cancel_tube_recalls(
    repo: ProcedureRecallRepository,
    patient_id: int,
    laterality: str,
    user_id: int,
) -> None:
    for row in await repo.list_open_for_patient(patient_id):
        if row.laterality != laterality or row.reason_key not in TUBE_REASON_KEYS:
            continue
        if row.status not in {"pending", "unreachable"}:
            continue
        row.status = "cancelled"
        row.cancelled_reason = _SUPERSEDED
        row.updated_by_id = user_id


async def _sync_flags(
    repo: PatientFlagRepository,
    user: CurrentUser,
    procedure: ProcedureRecord,
    active: list[PatientFlag],
    body: Write,
    devices: list[EarDevice],
    on: date,
) -> None:
    keep: set[tuple[str, str]] = set()
    for device in devices:
        if device.device_type == "ventilation_tube" and device.status == "in_place":
            keep.add((FLAG_TUBE, device.laterality))
        if device.device_type == "mastoid_cavity":
            keep.add((FLAG_CAVITY, device.laterality))
    for item in body.structures:
        if item.finding_code == CHOLESTEATOMA_CODE:
            keep.add((FLAG_CHOLESTEATOMA, item.laterality.value))
    owner = procedure.public_id
    for flag in active:
        detail = flag.detail if isinstance(flag.detail, dict) else {}
        if detail.get("procedurePublicId") != owner:
            continue
        if (flag.flag_code, flag.laterality) in keep:
            continue
        end_flag(flag, on, user.user_id)
    for code, laterality in keep:
        if any(
            flag.flag_code == code and flag.laterality == laterality for flag in active
        ):
            continue
        due = next(
            (
                device.next_check_due.isoformat()
                for device in devices
                if device.laterality == laterality
            ),
            None,
        )
        await repo.add(
            PatientFlag(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                patient_id=int(procedure.patient_id),
                flag_code=code,
                laterality=laterality,
                detail={"procedurePublicId": owner, "nextCheckDue": due},
                started_on=on,
                is_auto=True,
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
        )


def end_matching_flags(
    active: list[PatientFlag],
    code: str,
    laterality: str,
    on: date,
    user_id: int,
) -> None:
    for flag in active:
        if flag.flag_code == code and flag.laterality == laterality:
            end_flag(flag, on, user_id)


def end_flag(flag: PatientFlag, on: date, user_id: int) -> None:
    if flag.ended_on is not None:
        return
    flag.ended_on = on
    flag.updated_by_id = user_id
    flag.version = int(flag.version) + 1
