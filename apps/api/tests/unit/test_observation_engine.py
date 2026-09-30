"""Known-answer checks for observation value rules and bilateral expansion."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from ent.engines.observations.bilateral import (
    VERSION as BILATERAL_VERSION,
)
from ent.engines.observations.bilateral import (
    expand_bilateral_observations,
)
from ent.engines.observations.types import (
    ComponentDraft,
    ObservationDraft,
    ValueDraft,
)
from ent.engines.observations.validation import (
    VERSION as VALUE_VERSION,
)
from ent.engines.observations.validation import (
    ObservationValueError,
    validate_observation_value,
)

_WHEN = datetime(2026, 6, 1, 9, 0, 0)


def _finding(**overrides: object) -> ObservationDraft:
    value = ValueDraft(value_type="boolean", value_boolean=True)
    base = ObservationDraft(
        concept_code="FIND.TM.PERFORATION",
        body_site_code="ANAT.TM",
        map_region_code="tm.pars-tensa.antero-inferior",
        laterality="bilateral",
        status="abnormal",
        value=value,
        components=(
            ComponentDraft(
                concept_code="QUAL.SIZE",
                value=ValueDraft(
                    value_type="numeric",
                    value_numeric=Decimal("40"),
                    value_unit="%",
                ),
            ),
        ),
        effective_at=_WHEN,
        source="clinician",
        confirmed=True,
        method_concept_code=None,
    )
    laterality = overrides.get("laterality", base.laterality)
    return ObservationDraft(
        concept_code=base.concept_code,
        body_site_code=base.body_site_code,
        map_region_code=base.map_region_code,
        laterality=str(laterality),
        status=base.status,
        value=base.value,
        components=base.components,
        effective_at=base.effective_at,
        source=base.source,
        confirmed=base.confirmed,
        method_concept_code=base.method_concept_code,
    )


def test_engine_versions_are_recorded() -> None:
    assert BILATERAL_VERSION == "1.0.0"
    assert VALUE_VERSION == "1.0.0"


def test_bilateral_finding_becomes_one_row_per_side() -> None:
    expanded = expand_bilateral_observations([_finding()])
    assert [item.laterality for item in expanded] == ["right", "left"]
    assert expanded[0].components[0].value.value_numeric == Decimal("40")
    assert expanded[1].components == expanded[0].components
    assert expanded[0].map_region_code == "tm.pars-tensa.antero-inferior"


def test_midline_and_one_side_stay_a_single_row() -> None:
    items = expand_bilateral_observations(
        [_finding(laterality="right"), _finding(laterality="midline")]
    )
    assert [item.laterality for item in items] == ["right", "midline"]


def test_ordinal_grade_is_a_single_column() -> None:
    validate_observation_value(ValueDraft(value_type="ordinal", ordinal_value=3))


def test_boolean_false_is_a_recorded_value() -> None:
    validate_observation_value(ValueDraft(value_type="boolean", value_boolean=False))


def test_range_requires_ordered_bounds() -> None:
    validate_observation_value(
        ValueDraft(value_type="range", value_low=Decimal("1"), value_high=Decimal("4"))
    )
    with pytest.raises(ObservationValueError) as exc:
        validate_observation_value(
            ValueDraft(
                value_type="range",
                value_low=Decimal("4"),
                value_high=Decimal("1"),
            )
        )
    assert exc.value.reason == "value_range_order"


def test_mixed_value_columns_are_rejected() -> None:
    with pytest.raises(ObservationValueError) as exc:
        validate_observation_value(
            ValueDraft(value_type="ordinal", ordinal_value=3, value_text="grade 3")
        )
    assert exc.value.reason == "text"


def test_code_value_requires_a_concept_and_nothing_else() -> None:
    validate_observation_value(
        ValueDraft(value_type="code", value_concept_code="FIND.TM.EFFUSION")
    )
    with pytest.raises(ObservationValueError) as exc:
        validate_observation_value(ValueDraft(value_type="code"))
    assert exc.value.reason == "concept"


def test_each_value_type_rejects_a_foreign_column() -> None:
    with pytest.raises(ObservationValueError) as unknown:
        validate_observation_value(ValueDraft(value_type="blob"))
    assert unknown.value.reason == "value_type"

    validate_observation_value(
        ValueDraft(value_type="numeric", value_numeric=Decimal("12"), value_unit="mm")
    )
    validate_observation_value(ValueDraft(value_type="text", value_text="dry"))
    validate_observation_value(
        ValueDraft(
            value_type="range",
            value_low=Decimal("1"),
            value_high=Decimal("1"),
            value_unit="mm",
        )
    )

    rejected = (
        ValueDraft(
            value_type="code", value_concept_code="FIND.TM.EFFUSION", value_unit="mm"
        ),
        ValueDraft(value_type="boolean", value_boolean=True, value_unit="mm"),
        ValueDraft(value_type="text", value_text="dry", value_unit="mm"),
        ValueDraft(value_type="ordinal", ordinal_value=3, value_unit="mm"),
        ValueDraft(value_type="range", value_low=Decimal("1")),
        ValueDraft(value_type="range", value_high=Decimal("4")),
        ValueDraft(value_type="text", value_text="   "),
        ValueDraft(value_type="numeric"),
    )
    for value in rejected:
        with pytest.raises(ObservationValueError):
            validate_observation_value(value)
