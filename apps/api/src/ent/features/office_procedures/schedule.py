"""Which recorded dates become recalls.

Windows are the spans in feature spec appendix C. The due date is the date
stored on the form. No date is calculated here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ent.features.office_procedures.constants import (
    PACK_METHODS,
    PACK_WINDOW_DAYS,
    REASON_PACK,
    REASON_SIALENDOSCOPY,
    REASON_SPECIMEN,
    REASON_SPLINT,
    SIALENDOSCOPY_WINDOW_DAYS,
    SPECIMEN_WINDOW_DAYS,
    SPLINT_WINDOW_DAYS,
)
from ent.features.office_procedures.schemas.requests import (
    BiopsyWrite,
    EpistaxisWrite,
    FineNeedleAspirationWrite,
    NasalFractureWrite,
    ShortProcedureWrite,
    SialendoscopyWrite,
)
from ent.features.recalls.constants import RECALL_LATERALITIES


@dataclass(frozen=True, slots=True)
class PlannedRecall:
    reason_key: str
    due_on: date
    window_days: int
    laterality: str


def removal_due_date(detail: ShortProcedureWrite) -> date | None:
    if isinstance(detail, EpistaxisWrite) and detail.method in PACK_METHODS:
        return detail.pack_removal_date
    if isinstance(detail, NasalFractureWrite):
        return detail.splint_removal_date
    return None


def result_due_date(detail: ShortProcedureWrite) -> date | None:
    if isinstance(detail, FineNeedleAspirationWrite | BiopsyWrite):
        return detail.result_due_date
    return None


def planned_recalls(
    detail: ShortProcedureWrite,
    laterality: str,
) -> tuple[PlannedRecall, ...]:
    side = laterality if laterality in RECALL_LATERALITIES else "na"
    wanted: list[PlannedRecall] = []
    removal = removal_due_date(detail)
    if isinstance(detail, EpistaxisWrite) and removal is not None:
        wanted.append(
            PlannedRecall(REASON_PACK, removal, PACK_WINDOW_DAYS, side),
        )
    if isinstance(detail, NasalFractureWrite) and removal is not None:
        wanted.append(
            PlannedRecall(REASON_SPLINT, removal, SPLINT_WINDOW_DAYS, side),
        )
    specimen = result_due_date(detail)
    if specimen is not None:
        wanted.append(
            PlannedRecall(REASON_SPECIMEN, specimen, SPECIMEN_WINDOW_DAYS, side),
        )
    if isinstance(detail, SialendoscopyWrite):
        wanted.append(
            PlannedRecall(
                REASON_SIALENDOSCOPY,
                detail.follow_up_date,
                SIALENDOSCOPY_WINDOW_DAYS,
                side,
            )
        )
    return tuple(wanted)


def dates_before_procedure(
    detail: ShortProcedureWrite,
    performed_on: date,
) -> str | None:
    """Return a stable reason when a recorded date precedes the procedure day."""

    removal = removal_due_date(detail)
    if removal is not None and removal < performed_on:
        return "removal_before_procedure"
    specimen = result_due_date(detail)
    if specimen is not None and specimen < performed_on:
        return "result_before_procedure"
    if isinstance(detail, SialendoscopyWrite) and detail.follow_up_date < performed_on:
        return "follow_up_before_procedure"
    return None
