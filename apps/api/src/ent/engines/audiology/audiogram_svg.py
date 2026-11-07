"""Pure SVG audiogram plot for printed reports (feature spec §8.1, P4-07)."""

from __future__ import annotations

import base64
from collections.abc import Sequence
from math import log2
from typing import Literal

from ent.engines.audiology.types import ThresholdPoint

VERSION = "1.0.0"
CODE = "audiology.audiogram_svg"
REFERENCE = (
    "ISO 8253-1 / ASHA 2005 audiogram symbol conventions; "
    "Feature specification §8.1 & P4-04"
)
FORMULA = "Log-frequency × dB HL descending audiogram with standard ASHA symbols"

REF_HZ = 125
CHART_WIDTH = 720
CHART_HEIGHT = 420
PAD_LEFT = 48
PAD_RIGHT = 24
PAD_TOP = 24
PAD_BOTTOM = 40
MIN_LEVEL_DB = -10
MAX_LEVEL_DB = 130
RIGHT_COLOR = "#dc2626"
LEFT_COLOR = "#2563eb"

STANDARD_FREQUENCIES_HZ = (
    125,
    250,
    500,
    750,
    1000,
    1500,
    2000,
    3000,
    4000,
    6000,
    8000,
)
EXTENDED_HIGH_FREQUENCIES_HZ = (10000, 12500, 14000, 16000)
CHART_DB_TICKS = tuple(range(MIN_LEVEL_DB, MAX_LEVEL_DB + 1, 10))

_Ear = Literal["right", "left"]
_Conduction = Literal["air", "bone"]
_Series = tuple[_Ear, _Conduction, bool]


def frequencies_for_chart(has_extended_high_frequencies: bool) -> tuple[int, ...]:
    if has_extended_high_frequencies:
        return STANDARD_FREQUENCIES_HZ + EXTENDED_HIGH_FREQUENCIES_HZ
    return STANDARD_FREQUENCIES_HZ


def render_audiogram_svg(
    thresholds: Sequence[ThresholdPoint],
    *,
    has_extended_high_frequencies: bool,
) -> str:
    """Return SVG markup with explicit LTR layout (never mirrored in RTL PDFs)."""

    frequencies = frequencies_for_chart(has_extended_high_frequencies)
    points = _chart_points(thresholds)
    parts: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{CHART_WIDTH}" height="{CHART_HEIGHT}" '
        'viewBox="0 0 {0} {1}" direction="ltr" xml:lang="en">'.format(
            CHART_WIDTH,
            CHART_HEIGHT,
        ),
        _grid(frequencies),
    ]
    series: tuple[_Series, ...] = (
        ("right", "air", False),
        ("right", "air", True),
        ("left", "air", False),
        ("left", "air", True),
        ("right", "bone", False),
        ("right", "bone", True),
        ("left", "bone", False),
        ("left", "bone", True),
    )
    for ear, conduction, masked in series:
        connected = _connectable(points, ear, conduction, masked)
        if len(connected) >= 2:
            parts.append(_path(connected, frequencies, ear, conduction))
    for point in points:
        parts.append(_symbol(point, frequencies))
    parts.append("</svg>")
    return "".join(parts)


def render_audiogram_svg_data_uri(
    thresholds: Sequence[ThresholdPoint],
    *,
    has_extended_high_frequencies: bool,
) -> str:
    raw = render_audiogram_svg(
        thresholds,
        has_extended_high_frequencies=has_extended_high_frequencies,
    )
    encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _plot_width() -> float:
    return float(CHART_WIDTH - PAD_LEFT - PAD_RIGHT)


def _plot_height() -> float:
    return float(CHART_HEIGHT - PAD_TOP - PAD_BOTTOM)


def _frequency_x(frequency_hz: int, frequencies: Sequence[int]) -> float:
    width = _plot_width()
    min_hz = frequencies[0]
    max_hz = frequencies[-1]
    min_log = log2(min_hz / REF_HZ)
    max_log = log2(max_hz / REF_HZ)
    value_log = log2(frequency_hz / REF_HZ)
    if max_log == min_log:
        ratio = 0.0
    else:
        ratio = (value_log - min_log) / (max_log - min_log)
    return PAD_LEFT + ratio * width


def _level_y(level_db: int) -> float:
    height = _plot_height()
    ratio = (level_db - MIN_LEVEL_DB) / (MAX_LEVEL_DB - MIN_LEVEL_DB)
    return PAD_TOP + ratio * height


def _chart_points(thresholds: Sequence[ThresholdPoint]) -> list[ThresholdPoint]:
    plotted: list[ThresholdPoint] = []
    for row in thresholds:
        if row.is_no_response:
            level = row.level_db if row.level_db is not None else MAX_LEVEL_DB
            plotted.append(
                ThresholdPoint(
                    ear=row.ear,
                    conduction=row.conduction,
                    frequency_hz=row.frequency_hz,
                    level_db=level,
                    is_masked=row.is_masked,
                    is_no_response=True,
                )
            )
            continue
        if row.level_db is None:
            continue
        plotted.append(row)
    return plotted


def _connectable(
    points: Sequence[ThresholdPoint],
    ear: _Ear,
    conduction: _Conduction,
    is_masked: bool,
) -> list[ThresholdPoint]:
    filtered = [
        point
        for point in points
        if point.ear == ear
        and point.conduction == conduction
        and point.is_masked == is_masked
        and not point.is_no_response
    ]
    filtered.sort(key=lambda row: row.frequency_hz)
    return filtered


def _path(
    points: Sequence[ThresholdPoint],
    frequencies: Sequence[int],
    ear: _Ear,
    conduction: _Conduction,
) -> str:
    color = RIGHT_COLOR if ear == "right" else LEFT_COLOR
    commands = [
        f"{'M' if index == 0 else 'L'} {_frequency_x(row.frequency_hz, frequencies):.2f} {_level_y(int(row.level_db or 0)):.2f}"
        for index, row in enumerate(points)
    ]
    dash = ' stroke-dasharray="5 4"' if conduction == "bone" else ""
    return (
        f'<path d="{" ".join(commands)}" fill="none" stroke="{color}" '
        f'stroke-width="1.5"{dash}/>'
    )


def _grid(frequencies: Sequence[int]) -> str:
    lines: list[str] = []
    x2 = CHART_WIDTH - PAD_RIGHT
    y_bottom = CHART_HEIGHT - PAD_BOTTOM
    for tick in CHART_DB_TICKS:
        y = _level_y(tick)
        stroke = "#94a3b8" if tick == 0 else "#e2e8f0"
        width = "1.5" if tick in {0, 20} else "1"
        dash = "" if tick in {0, 20} else ' stroke-dasharray="4 4"'
        lines.append(
            f'<line x1="{PAD_LEFT}" y1="{y:.2f}" x2="{x2}" y2="{y:.2f}" '
            f'stroke="{stroke}" stroke-width="{width}"{dash}/>'
        )
        lines.append(
            f'<text x="8" y="{y + 4:.2f}" font-size="10" fill="#64748b">{tick}</text>'
        )
    for hz in frequencies:
        x = _frequency_x(hz, frequencies)
        lines.append(
            f'<line x1="{x:.2f}" y1="{PAD_TOP}" x2="{x:.2f}" y2="{y_bottom}" '
            f'stroke="#e2e8f0" stroke-width="1"/>'
        )
        label = _frequency_label(hz)
        lines.append(
            f'<text x="{x:.2f}" y="{CHART_HEIGHT - 12}" text-anchor="middle" '
            f'font-size="10" fill="#64748b">{label}</text>'
        )
    return "".join(lines)


def _frequency_label(hz: int) -> str:
    if hz >= 1000:
        value = hz / 1000
        if value.is_integer():
            return f"{int(value)}k"
        return f"{value:.1f}k"
    return str(hz)


def _symbol(point: ThresholdPoint, frequencies: Sequence[int]) -> str:
    x = _frequency_x(point.frequency_hz, frequencies)
    y = _level_y(int(point.level_db or MAX_LEVEL_DB))
    color = RIGHT_COLOR if point.ear == "right" else LEFT_COLOR
    size = 7
    core = _symbol_core(point, color, size)
    arrow = ""
    if point.is_no_response:
        if point.ear == "right":
            arrow = (
                f'<line x1="{x - size:.2f}" y1="{y + size + 2:.2f}" '
                f'x2="{x + size + 4:.2f}" y2="{y + size + 10:.2f}" '
                f'stroke="{color}" stroke-width="1.5"/>'
            )
        else:
            arrow = (
                f'<line x1="{x - size:.2f}" y1="{y + size + 2:.2f}" '
                f'x2="{x - size - 4:.2f}" y2="{y + size + 10:.2f}" '
                f'stroke="{color}" stroke-width="1.5"/>'
            )
    return f'<g transform="translate({x:.2f},{y:.2f})">{core}{arrow}</g>'


def _symbol_core(point: ThresholdPoint, color: str, size: int) -> str:
    if point.conduction == "air":
        if point.ear == "right":
            if point.is_masked:
                return (
                    f'<polygon points="0,{-size} {size},{size} {-size},{size}" '
                    f'fill="none" stroke="{color}" stroke-width="1.5"/>'
                )
            return (
                f'<circle r="{size}" fill="none" stroke="{color}" stroke-width="1.5"/>'
            )
        if point.is_masked:
            return (
                f'<rect x="{-size}" y="{-size}" width="{size * 2}" height="{size * 2}" '
                f'fill="none" stroke="{color}" stroke-width="1.5"/>'
            )
        return (
            f'<line x1="{-size}" y1="{-size}" x2="{size}" y2="{size}" '
            f'stroke="{color}" stroke-width="1.5"/>'
            f'<line x1="{-size}" y1="{size}" x2="{size}" y2="{-size}" '
            f'stroke="{color}" stroke-width="1.5"/>'
        )
    if point.ear == "right":
        if point.is_masked:
            return (
                f'<line x1="{-size - 2}" y1="{-size}" x2="{-size - 2}" y2="{size}" '
                f'stroke="{color}" stroke-width="1.5"/>'
                f'<line x1="{size + 2}" y1="{-size}" x2="{size + 2}" y2="{size}" '
                f'stroke="{color}" stroke-width="1.5"/>'
            )
        return (
            f'<line x1="{-size - 2}" y1="{-size}" x2="{-size - 2}" y2="{size}" '
            f'stroke="{color}" stroke-width="1.5"/>'
            f'<line x1="{size}" y1="{-size}" x2="{-size}" y2="0" '
            f'stroke="{color}" stroke-width="1.5"/>'
        )
    if point.is_masked:
        return (
            f'<line x1="{size + 2}" y1="{-size}" x2="{size + 2}" y2="{size}" '
            f'stroke="{color}" stroke-width="1.5"/>'
            f'<line x1="{-size - 2}" y1="{-size}" x2="{-size - 2}" y2="{size}" '
            f'stroke="{color}" stroke-width="1.5"/>'
        )
    return (
        f'<line x1="{size + 2}" y1="{-size}" x2="{size + 2}" y2="{size}" '
        f'stroke="{color}" stroke-width="1.5"/>'
        f'<line x1="{-size}" y1="{-size}" x2="{size}" y2="0" '
        f'stroke="{color}" stroke-width="1.5"/>'
    )
