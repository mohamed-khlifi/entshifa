"""Unit tests for audiology engine branches not reachable from fixtures alone."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

from ent.engines.audiology.errors import AudiometryInputError
from ent.engines.audiology.loss_type import classify_loss_type
from ent.engines.audiology.metrics import compute_audiogram_metrics
from ent.engines.audiology.thresholds import index_thresholds
from ent.engines.audiology.types import AsymmetryRule
from tests.clinical.test_audiology_engines import _air


def test_loss_type_mixed_when_bone_levels_missing_despite_gaps() -> None:
    indexed = index_thresholds([_air("right", 1000, 20)])
    gaps = {500: Decimal("20"), 1000: Decimal("18")}
    with (
        patch(
            "ent.engines.audiology.loss_type.gaps_for_ear",
            return_value=gaps,
        ),
        patch(
            "ent.engines.audiology.loss_type.optional_levels",
            return_value={},
        ),
    ):
        assert classify_loss_type(indexed, ear="right") == "mixed"


def test_metrics_optional_loss_and_config_on_incomplete_data() -> None:
    rule = AsymmetryRule(adjacent_db=15, adjacent_count=2, single_db=20, wrs_percent=15)
    thresholds = [_air("right", 1000, 20)]
    with (
        patch(
            "ent.engines.audiology.metrics.classify_loss_type",
            side_effect=AudiometryInputError("audiology.incomplete_threshold"),
        ),
        patch(
            "ent.engines.audiology.metrics.describe_configuration",
            side_effect=AudiometryInputError("audiology.incomplete_threshold"),
        ),
    ):
        metrics = compute_audiogram_metrics(
            thresholds=thresholds,
            pta_formula="4freq_who",
            asymmetry_rule=rule,
            shift_rule="asha",
        )
    assert metrics.loss_type_right is None
    assert metrics.configuration_right is None
