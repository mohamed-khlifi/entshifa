"""Error translation paths in evaluate_calculator."""

from __future__ import annotations

import pytest

from ent.engines import calculator_catalog as catalog
from ent.engines.audiology.errors import AudiometryInputError
from ent.engines.calculator_errors import CalculatorInputError
from ent.engines.endoscopy.errors import ScoreInputError
from ent.engines.laryngoscopy.errors import ScoreInputError as LScoreInputError
from ent.engines.prescriptions.errors import EngineInputError


@pytest.mark.clinical
def test_evaluate_maps_audiometry_input_error() -> None:
    def _boom(_raw: object) -> object:
        raise AudiometryInputError(code="audiometry.test")

    spec, _ = catalog._CATALOG["audiology.pta"]
    catalog._CATALOG["audiology.pta"] = (spec, _boom)
    try:
        with pytest.raises(CalculatorInputError) as exc:
            catalog.evaluate_calculator("audiology.pta", {})
        assert exc.value.code == "calculator.clinical_input"
    finally:
        catalog._CATALOG["audiology.pta"] = (spec, catalog._run_pta)


@pytest.mark.clinical
def test_evaluate_maps_endoscopy_score_input_error() -> None:
    def _boom(_raw: object) -> object:
        raise ScoreInputError(code="score.test", message="invalid")

    spec, _ = catalog._CATALOG["endoscopy.adenoid_obstruction"]
    catalog._CATALOG["endoscopy.adenoid_obstruction"] = (spec, _boom)
    try:
        with pytest.raises(CalculatorInputError) as exc:
            catalog.evaluate_calculator("endoscopy.adenoid_obstruction", {"percent": 1})
        assert exc.value.code == "calculator.clinical_input"
    finally:
        catalog._CATALOG["endoscopy.adenoid_obstruction"] = (
            spec,
            catalog._run_adenoid,
        )


@pytest.mark.clinical
def test_evaluate_maps_laryngoscopy_score_input_error() -> None:
    def _boom(_raw: object) -> object:
        raise LScoreInputError(code="voice.test", message="invalid")

    spec, _ = catalog._CATALOG["laryngoscopy.grbas"]
    catalog._CATALOG["laryngoscopy.grbas"] = (spec, _boom)
    try:
        with pytest.raises(CalculatorInputError) as exc:
            catalog.evaluate_calculator("laryngoscopy.grbas", {})
        assert exc.value.code == "calculator.clinical_input"
    finally:
        catalog._CATALOG["laryngoscopy.grbas"] = (spec, catalog._run_grbas)


@pytest.mark.clinical
def test_evaluate_maps_prescription_engine_input_error() -> None:
    def _boom(_raw: object) -> object:
        raise EngineInputError(code="rx.test")

    spec, _ = catalog._CATALOG["endoscopy.adenoid_obstruction"]
    catalog._CATALOG["endoscopy.adenoid_obstruction"] = (spec, _boom)
    try:
        with pytest.raises(CalculatorInputError) as exc:
            catalog.evaluate_calculator("endoscopy.adenoid_obstruction", {"percent": 1})
        assert exc.value.code == "calculator.clinical_input"
    finally:
        catalog._CATALOG["endoscopy.adenoid_obstruction"] = (
            spec,
            catalog._run_adenoid,
        )


@pytest.mark.clinical
def test_evaluate_maps_airway_input_error() -> None:
    from ent.engines.airway.errors import AirwayInputError

    def _boom(_raw: object) -> object:
        raise AirwayInputError("airway.ett_age_out_of_range")

    spec, _ = catalog._CATALOG["airway.ett_size"]
    catalog._CATALOG["airway.ett_size"] = (spec, _boom)
    try:
        with pytest.raises(CalculatorInputError) as exc:
            catalog.evaluate_calculator(
                "airway.ett_size",
                {"age_years": "6", "cuffed": "true"},
            )
        assert exc.value.code == "calculator.clinical_input"
    finally:
        catalog._CATALOG["airway.ett_size"] = (spec, catalog._run_ett_size)


@pytest.mark.clinical
def test_evaluate_maps_general_input_error() -> None:
    from ent.engines.general.errors import GeneralCalculatorInputError

    def _boom(_raw: object) -> object:
        raise GeneralCalculatorInputError("general.bmi_input_invalid")

    spec, _ = catalog._CATALOG["general.bmi"]
    catalog._CATALOG["general.bmi"] = (spec, _boom)
    try:
        with pytest.raises(CalculatorInputError) as exc:
            catalog.evaluate_calculator(
                "general.bmi",
                {"weight_kg": "70", "height_cm": "170"},
            )
        assert exc.value.code == "calculator.clinical_input"
    finally:
        catalog._CATALOG["general.bmi"] = (spec, catalog._run_bmi)


@pytest.mark.clinical
def test_evaluate_unexpected_error_propagates() -> None:
    def _boom(_raw: object) -> object:
        raise RuntimeError("unexpected")

    spec, _ = catalog._CATALOG["endoscopy.adenoid_obstruction"]
    catalog._CATALOG["endoscopy.adenoid_obstruction"] = (spec, _boom)
    try:
        with pytest.raises(RuntimeError, match="unexpected"):
            catalog.evaluate_calculator("endoscopy.adenoid_obstruction", {"percent": 1})
    finally:
        catalog._CATALOG["endoscopy.adenoid_obstruction"] = (
            spec,
            catalog._run_adenoid,
        )
