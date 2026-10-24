"""Calculator catalog. The generic calculator HTTP API arrives in phase 5."""

from __future__ import annotations

from dataclasses import dataclass

from ent.engines.audiology.air_bone_gap import CODE as ABG_CODE
from ent.engines.audiology.air_bone_gap import FORMULA as ABG_FORMULA
from ent.engines.audiology.air_bone_gap import REFERENCE as ABG_REFERENCE
from ent.engines.audiology.air_bone_gap import VERSION as ABG_VERSION
from ent.engines.audiology.asymmetry import CODE as ASYMMETRY_CODE
from ent.engines.audiology.asymmetry import FORMULA as ASYMMETRY_FORMULA
from ent.engines.audiology.asymmetry import REFERENCE as ASYMMETRY_REFERENCE
from ent.engines.audiology.asymmetry import VERSION as ASYMMETRY_VERSION
from ent.engines.audiology.impairment import CODE as IMPAIRMENT_CODE
from ent.engines.audiology.impairment import FORMULA as IMPAIRMENT_FORMULA
from ent.engines.audiology.impairment import REFERENCE as IMPAIRMENT_REFERENCE
from ent.engines.audiology.impairment import VERSION as IMPAIRMENT_VERSION
from ent.engines.audiology.interaural import CODE as INTERAURAL_CODE
from ent.engines.audiology.interaural import FORMULA as INTERAURAL_FORMULA
from ent.engines.audiology.interaural import REFERENCE as INTERAURAL_REFERENCE
from ent.engines.audiology.interaural import VERSION as INTERAURAL_VERSION
from ent.engines.audiology.loss_type import CODE as LOSS_TYPE_CODE
from ent.engines.audiology.loss_type import FORMULA as LOSS_TYPE_FORMULA
from ent.engines.audiology.loss_type import REFERENCE as LOSS_TYPE_REFERENCE
from ent.engines.audiology.loss_type import VERSION as LOSS_TYPE_VERSION
from ent.engines.audiology.pta import CODE as PTA_CODE
from ent.engines.audiology.pta import FORMULA as PTA_FORMULA
from ent.engines.audiology.pta import REFERENCE as PTA_REFERENCE
from ent.engines.audiology.pta import VERSION as PTA_VERSION
from ent.engines.audiology.speech_agreement import CODE as SPEECH_CODE
from ent.engines.audiology.speech_agreement import FORMULA as SPEECH_FORMULA
from ent.engines.audiology.speech_agreement import REFERENCE as SPEECH_REFERENCE
from ent.engines.audiology.speech_agreement import VERSION as SPEECH_VERSION
from ent.engines.audiology.threshold_shift import CODE as SHIFT_CODE
from ent.engines.audiology.threshold_shift import FORMULA as SHIFT_FORMULA
from ent.engines.audiology.threshold_shift import REFERENCE as SHIFT_REFERENCE
from ent.engines.audiology.threshold_shift import VERSION as SHIFT_VERSION
from ent.engines.audiology.who_grading import CODE as WHO_CODE
from ent.engines.audiology.who_grading import FORMULA as WHO_FORMULA
from ent.engines.audiology.who_grading import REFERENCE as WHO_REFERENCE
from ent.engines.audiology.who_grading import VERSION as WHO_VERSION
from ent.engines.endoscopy.adenoid import CODE as ADENOID_CODE
from ent.engines.endoscopy.adenoid import FORMULA as ADENOID_FORMULA
from ent.engines.endoscopy.adenoid import REFERENCE as ADENOID_REFERENCE
from ent.engines.endoscopy.adenoid import VERSION as ADENOID_VERSION
from ent.engines.endoscopy.lund_kennedy import CODE as LK_CODE
from ent.engines.endoscopy.lund_kennedy import FORMULA as LK_FORMULA
from ent.engines.endoscopy.lund_kennedy import REFERENCE as LK_REFERENCE
from ent.engines.endoscopy.lund_kennedy import VERSION as LK_VERSION
from ent.engines.endoscopy.modified_lund_kennedy import CODE as MODIFIED_LK_CODE
from ent.engines.endoscopy.modified_lund_kennedy import FORMULA as MODIFIED_LK_FORMULA
from ent.engines.endoscopy.modified_lund_kennedy import (
    REFERENCE as MODIFIED_LK_REFERENCE,
)
from ent.engines.endoscopy.modified_lund_kennedy import VERSION as MODIFIED_LK_VERSION
from ent.engines.endoscopy.polyp_grade import CODE as POLYP_CODE
from ent.engines.endoscopy.polyp_grade import FORMULA as POLYP_FORMULA
from ent.engines.endoscopy.polyp_grade import REFERENCE as POLYP_REFERENCE
from ent.engines.endoscopy.polyp_grade import VERSION as POLYP_VERSION
from ent.engines.laryngoscopy.grbas import CODE as GRBAS_CODE
from ent.engines.laryngoscopy.grbas import FORMULA as GRBAS_FORMULA
from ent.engines.laryngoscopy.grbas import REFERENCE as GRBAS_REFERENCE
from ent.engines.laryngoscopy.grbas import VERSION as GRBAS_VERSION
from ent.engines.laryngoscopy.penetration_aspiration import CODE as PAS_CODE
from ent.engines.laryngoscopy.penetration_aspiration import FORMULA as PAS_FORMULA
from ent.engines.laryngoscopy.penetration_aspiration import (
    REFERENCE as PAS_REFERENCE,
)
from ent.engines.laryngoscopy.penetration_aspiration import VERSION as PAS_VERSION
from ent.engines.laryngoscopy.reflux_finding_score import CODE as RFS_CODE
from ent.engines.laryngoscopy.reflux_finding_score import FORMULA as RFS_FORMULA
from ent.engines.laryngoscopy.reflux_finding_score import REFERENCE as RFS_REFERENCE
from ent.engines.laryngoscopy.reflux_finding_score import VERSION as RFS_VERSION
from ent.engines.prescriptions.pediatric_dosing import (
    CODE as PEDIATRIC_CODE,
)
from ent.engines.prescriptions.pediatric_dosing import (
    FORMULA as PEDIATRIC_FORMULA,
)
from ent.engines.prescriptions.pediatric_dosing import (
    REFERENCE as PEDIATRIC_REFERENCE,
)
from ent.engines.prescriptions.pediatric_dosing import (
    VERSION as PEDIATRIC_VERSION,
)
from ent.engines.prescriptions.steroid_taper import CODE as TAPER_CODE
from ent.engines.prescriptions.steroid_taper import FORMULA as TAPER_FORMULA
from ent.engines.prescriptions.steroid_taper import REFERENCE as TAPER_REFERENCE
from ent.engines.prescriptions.steroid_taper import VERSION as TAPER_VERSION
from ent.engines.recalls.protocol_resolver import CODE as PROTOCOL_RESOLVER_CODE
from ent.engines.recalls.protocol_resolver import (
    FORMULA as PROTOCOL_RESOLVER_FORMULA,
)
from ent.engines.recalls.protocol_resolver import (
    REFERENCE as PROTOCOL_RESOLVER_REFERENCE,
)
from ent.engines.recalls.protocol_resolver import VERSION as PROTOCOL_RESOLVER_VERSION


@dataclass(frozen=True, slots=True)
class CalculatorSpec:
    code: str
    version: str
    reference: str
    unit: str | None
    formula: str


def registered_calculators() -> tuple[CalculatorSpec, ...]:
    """Metadata for engines that must stay discoverable without new UI code."""

    return (
        CalculatorSpec(
            code=PEDIATRIC_CODE,
            version=PEDIATRIC_VERSION,
            reference=PEDIATRIC_REFERENCE,
            unit="mg",
            formula=PEDIATRIC_FORMULA,
        ),
        CalculatorSpec(
            code=TAPER_CODE,
            version=TAPER_VERSION,
            reference=TAPER_REFERENCE,
            unit="day",
            formula=TAPER_FORMULA,
        ),
        CalculatorSpec(
            code=LK_CODE,
            version=LK_VERSION,
            reference=LK_REFERENCE,
            unit="points",
            formula=LK_FORMULA,
        ),
        CalculatorSpec(
            code=MODIFIED_LK_CODE,
            version=MODIFIED_LK_VERSION,
            reference=MODIFIED_LK_REFERENCE,
            unit="points",
            formula=MODIFIED_LK_FORMULA,
        ),
        CalculatorSpec(
            code=POLYP_CODE,
            version=POLYP_VERSION,
            reference=POLYP_REFERENCE,
            unit="grade",
            formula=POLYP_FORMULA,
        ),
        CalculatorSpec(
            code=ADENOID_CODE,
            version=ADENOID_VERSION,
            reference=ADENOID_REFERENCE,
            unit="%",
            formula=ADENOID_FORMULA,
        ),
        CalculatorSpec(
            code=RFS_CODE,
            version=RFS_VERSION,
            reference=RFS_REFERENCE,
            unit="points",
            formula=RFS_FORMULA,
        ),
        CalculatorSpec(
            code=GRBAS_CODE,
            version=GRBAS_VERSION,
            reference=GRBAS_REFERENCE,
            unit="points",
            formula=GRBAS_FORMULA,
        ),
        CalculatorSpec(
            code=PAS_CODE,
            version=PAS_VERSION,
            reference=PAS_REFERENCE,
            unit="grade",
            formula=PAS_FORMULA,
        ),
        CalculatorSpec(
            code=PROTOCOL_RESOLVER_CODE,
            version=PROTOCOL_RESOLVER_VERSION,
            reference=PROTOCOL_RESOLVER_REFERENCE,
            unit="recall",
            formula=PROTOCOL_RESOLVER_FORMULA,
        ),
        CalculatorSpec(
            code=PTA_CODE,
            version=PTA_VERSION,
            reference=PTA_REFERENCE,
            unit="dB HL",
            formula=PTA_FORMULA,
        ),
        CalculatorSpec(
            code=ABG_CODE,
            version=ABG_VERSION,
            reference=ABG_REFERENCE,
            unit="dB",
            formula=ABG_FORMULA,
        ),
        CalculatorSpec(
            code=WHO_CODE,
            version=WHO_VERSION,
            reference=WHO_REFERENCE,
            unit=None,
            formula=WHO_FORMULA,
        ),
        CalculatorSpec(
            code=LOSS_TYPE_CODE,
            version=LOSS_TYPE_VERSION,
            reference=LOSS_TYPE_REFERENCE,
            unit=None,
            formula=LOSS_TYPE_FORMULA,
        ),
        CalculatorSpec(
            code=INTERAURAL_CODE,
            version=INTERAURAL_VERSION,
            reference=INTERAURAL_REFERENCE,
            unit="dB",
            formula=INTERAURAL_FORMULA,
        ),
        CalculatorSpec(
            code=IMPAIRMENT_CODE,
            version=IMPAIRMENT_VERSION,
            reference=IMPAIRMENT_REFERENCE,
            unit="%",
            formula=IMPAIRMENT_FORMULA,
        ),
        CalculatorSpec(
            code=ASYMMETRY_CODE,
            version=ASYMMETRY_VERSION,
            reference=ASYMMETRY_REFERENCE,
            unit=None,
            formula=ASYMMETRY_FORMULA,
        ),
        CalculatorSpec(
            code=SHIFT_CODE,
            version=SHIFT_VERSION,
            reference=SHIFT_REFERENCE,
            unit=None,
            formula=SHIFT_FORMULA,
        ),
        CalculatorSpec(
            code=SPEECH_CODE,
            version=SPEECH_VERSION,
            reference=SPEECH_REFERENCE,
            unit=None,
            formula=SPEECH_FORMULA,
        ),
    )
