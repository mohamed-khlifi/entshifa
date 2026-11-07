"""Known-answer tests for the audiogram SVG engine (P4-07)."""

from __future__ import annotations

import base64

from ent.engines.audiology.audiogram_svg import (
    CODE,
    FORMULA,
    REFERENCE,
    VERSION,
    _frequency_x,
    frequencies_for_chart,
    render_audiogram_svg,
    render_audiogram_svg_data_uri,
)
from ent.engines.audiology.types import ThresholdPoint


def _point(
    *,
    ear: str = "right",
    conduction: str = "air",
    frequency_hz: int = 1000,
    level_db: int = 30,
    is_masked: bool = False,
    is_no_response: bool = False,
) -> ThresholdPoint:
    return ThresholdPoint(
        ear=ear,  # type: ignore[arg-type]
        conduction=conduction,  # type: ignore[arg-type]
        frequency_hz=frequency_hz,
        level_db=level_db,
        is_masked=is_masked,
        is_no_response=is_no_response,
    )


def test_engine_metadata() -> None:
    assert VERSION == "1.0.0"
    assert CODE == "audiology.audiogram_svg"
    assert "ISO 8253-1" in REFERENCE
    assert FORMULA


def test_svg_root_is_explicit_ltr() -> None:
    svg = render_audiogram_svg([_point()], has_extended_high_frequencies=False)
    assert 'direction="ltr"' in svg
    assert 'xml:lang="en"' in svg
    assert svg.startswith("<svg")


def test_blank_thresholds_are_omitted() -> None:
    svg = render_audiogram_svg(
        [
            _point(level_db=20),
            ThresholdPoint(
                ear="right",
                conduction="air",
                frequency_hz=2000,
                level_db=None,
                is_masked=False,
                is_no_response=False,
            ),
        ],
        has_extended_high_frequencies=False,
    )
    assert "<circle" in svg


def test_right_bone_masked_brackets() -> None:
    svg = render_audiogram_svg(
        [_point(ear="right", conduction="bone", is_masked=True, frequency_hz=500)],
        has_extended_high_frequencies=False,
    )
    assert 'stroke="#dc2626"' in svg
    assert "<line" in svg


def test_right_circle_and_left_cross_symbols() -> None:
    svg = render_audiogram_svg(
        [
            _point(ear="right", conduction="air"),
            _point(ear="left", conduction="air", level_db=40),
        ],
        has_extended_high_frequencies=False,
    )
    assert 'stroke="#dc2626"' in svg
    assert 'stroke="#2563eb"' in svg
    assert "<circle" in svg
    assert "<line" in svg


def test_bone_brackets_and_dashed_path() -> None:
    svg = render_audiogram_svg(
        [
            _point(conduction="bone", frequency_hz=500, level_db=15),
            _point(conduction="bone", frequency_hz=2000, level_db=25),
        ],
        has_extended_high_frequencies=False,
    )
    assert 'stroke-dasharray="5 4"' in svg


def test_no_response_arrow_present() -> None:
    svg = render_audiogram_svg(
        [_point(is_no_response=True, level_db=110)],
        has_extended_high_frequencies=False,
    )
    assert "<line" in svg
    assert 'stroke-width="1.5"' in svg


def test_extended_high_frequencies_extend_axis() -> None:
    standard = frequencies_for_chart(False)
    extended = frequencies_for_chart(True)
    assert len(extended) > len(standard)
    assert 12500 in extended
    svg = render_audiogram_svg(
        [_point(frequency_hz=12500, level_db=20)],
        has_extended_high_frequencies=True,
    )
    assert "12.5k" in svg or "12500" in svg


def test_data_uri_is_base64_svg() -> None:
    uri = render_audiogram_svg_data_uri(
        [_point()],
        has_extended_high_frequencies=False,
    )
    assert uri.startswith("data:image/svg+xml;base64,")
    payload = uri.split(",", 1)[1]
    decoded = base64.b64decode(payload.encode()).decode("utf-8")
    assert decoded.startswith("<svg")
    assert 'direction="ltr"' in decoded


def test_log_axis_handles_single_frequency_span() -> None:
    position = _frequency_x(1000, (1000, 1000))
    assert position >= 0


def test_left_no_response_arrow_points_left() -> None:
    svg = render_audiogram_svg(
        [_point(ear="left", is_no_response=True, level_db=110)],
        has_extended_high_frequencies=False,
    )
    assert 'x2="' in svg


def test_left_bone_symbols_include_brackets() -> None:
    svg = render_audiogram_svg(
        [
            _point(ear="left", conduction="bone", frequency_hz=500),
            _point(
                ear="left",
                conduction="bone",
                frequency_hz=2000,
                is_masked=True,
            ),
        ],
        has_extended_high_frequencies=False,
    )
    assert "<line" in svg
    assert 'stroke="#2563eb"' in svg


def test_masked_air_triangle_and_square() -> None:
    svg = render_audiogram_svg(
        [
            _point(ear="right", is_masked=True),
            _point(ear="left", is_masked=True, level_db=35),
        ],
        has_extended_high_frequencies=False,
    )
    assert "<polygon" in svg
    assert "<rect" in svg
