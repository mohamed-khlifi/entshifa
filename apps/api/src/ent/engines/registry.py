"""Calculator catalog. The generic calculator HTTP API arrives in phase 5."""

from __future__ import annotations

from dataclasses import dataclass

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
    )
