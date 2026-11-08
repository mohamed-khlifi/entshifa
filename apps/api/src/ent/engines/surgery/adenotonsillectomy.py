"""Pediatric OSA adenotonsillectomy discussion checklist (feature spec §12.3)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ent.engines.results import CalculationResult, Flag
from ent.engines.surgery.errors import SurgeryChecklistInputError

VERSION = "1.0.0"
CODE = "surgery.adenotonsillectomy_osa"
REFERENCE = (
    "Mitchell RB et al. AAO-HNS tonsillectomy guideline 2019; "
    "Marcus CL et al. AAP pediatric OSA guideline Pediatrics 2012. "
    "Feature specification §12.3. # VERIFY: local PSG AHI threshold."
)
FORMULA = (
    "SDB symptoms AND adenotonsillar hypertrophy AND "
    "(PSG AHI >= 1 OR clinical OSA without PSG); flag inpatient monitoring per risk"
)
PSG_AHI_THRESHOLD = Decimal("1")
SEVERE_AHI = Decimal("10")


@dataclass(frozen=True, slots=True)
class AdenotonsillectomyInput:
    sdb_symptoms_present: bool
    tonsil_brodsky_grade: int
    adenoid_hypertrophy: bool
    psg_performed: bool
    psg_ahi: Decimal | None
    age_under_3_years: bool
    high_risk_comorbidity: bool


def _hypertrophy(data: AdenotonsillectomyInput) -> bool:
    return data.tonsil_brodsky_grade >= 3 or data.adenoid_hypertrophy


def _psg_supports(data: AdenotonsillectomyInput) -> tuple[bool, bool]:
    if data.psg_performed:
        if data.psg_ahi is None:
            raise SurgeryChecklistInputError("surgery.osa_psg_ahi_required")
        if data.psg_ahi < Decimal("0") or data.psg_ahi > Decimal("200"):
            raise SurgeryChecklistInputError("surgery.osa_psg_ahi_out_of_range")
        return data.psg_ahi >= PSG_AHI_THRESHOLD, False
    return data.sdb_symptoms_present and _hypertrophy(data), True


def evaluate_adenotonsillectomy(
    data: AdenotonsillectomyInput,
) -> tuple[bool, tuple[Flag, ...]]:
    if data.tonsil_brodsky_grade < 0 or data.tonsil_brodsky_grade > 4:
        raise SurgeryChecklistInputError(
            "surgery.brodsky_grade_out_of_range",
            field="tonsil_brodsky_grade",
        )
    hypertrophy = _hypertrophy(data)
    psg_ok, psg_recommended = _psg_supports(data)
    candidacy = data.sdb_symptoms_present and hypertrophy and psg_ok
    severe = data.psg_ahi is not None and data.psg_ahi >= SEVERE_AHI
    inpatient = data.age_under_3_years or severe or data.high_risk_comorbidity
    flags: list[Flag] = [
        Flag(code="candidacy_met", detail={"met": str(candidacy).lower()}),
        Flag(
            code="psg_recommended_before_surgery",
            detail={"met": str(psg_recommended and not data.psg_performed).lower()},
        ),
        Flag(
            code="inpatient_monitoring_recommended",
            detail={"met": str(inpatient).lower()},
        ),
    ]
    if candidacy:
        flags.append(Flag(code="adenotonsillectomy_discussion_met", detail={}))
    return candidacy, tuple(flags)


def adenotonsillectomy_checklist(data: AdenotonsillectomyInput) -> CalculationResult:
    met, flags = evaluate_adenotonsillectomy(data)
    return CalculationResult(
        code=CODE,
        value="met" if met else "not_met",
        unit=None,
        inputs={
            "sdb_symptoms_present": str(data.sdb_symptoms_present).lower(),
            "tonsil_brodsky_grade": str(data.tonsil_brodsky_grade),
            "adenoid_hypertrophy": str(data.adenoid_hypertrophy).lower(),
            "psg_performed": str(data.psg_performed).lower(),
            "psg_ahi": "" if data.psg_ahi is None else format(data.psg_ahi, "f"),
            "age_under_3_years": str(data.age_under_3_years).lower(),
            "high_risk_comorbidity": str(data.high_risk_comorbidity).lower(),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=flags,
    )
