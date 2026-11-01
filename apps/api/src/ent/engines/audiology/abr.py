"""ABR latency and interaural wave V metrics (feature spec §8.4)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ent.engines.audiology.errors import AudiometryInputError
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "audiology.abr_latencies"
REFERENCE = "Feature specification §8.4 (ABR interpeak intervals and interaural wave V)"
FORMULA = (
    "i_iii = III-I, iii_v = V-III, i_v = V-I; "
    "interaural_v_diff = |V_right - V_left|; flag when diff > threshold_ms"
)

DEFAULT_INTERAURAL_V_THRESHOLD_MS = Decimal("0.30")


@dataclass(frozen=True, slots=True)
class AbrWaveInput:
    wave_i_ms: Decimal | None
    wave_iii_ms: Decimal | None
    wave_v_ms: Decimal | None


@dataclass(frozen=True, slots=True)
class AbrMetricsResult:
    i_iii_ms: Decimal | None
    iii_v_ms: Decimal | None
    i_v_ms: Decimal | None
    interaural_v_diff_ms: Decimal | None
    interaural_v_flag: bool
    flags: tuple[Flag, ...]


def _interval(later: Decimal | None, earlier: Decimal | None) -> Decimal | None:
    if later is None or earlier is None:
        return None
    if later < earlier:
        raise AudiometryInputError(
            "audiology.abr_invalid_wave_order",
            earlier=str(earlier),
            later=str(later),
        )
    return later - earlier


def compute_abr_metrics(
    waves: AbrWaveInput,
    *,
    contralateral_wave_v_ms: Decimal | None = None,
    threshold_ms: Decimal = DEFAULT_INTERAURAL_V_THRESHOLD_MS,
) -> AbrMetricsResult:
    i_iii = _interval(waves.wave_iii_ms, waves.wave_i_ms)
    iii_v = _interval(waves.wave_v_ms, waves.wave_iii_ms)
    i_v = _interval(waves.wave_v_ms, waves.wave_i_ms)

    interaural_diff: Decimal | None = None
    interaural_flag = False
    flags: list[Flag] = []
    if waves.wave_v_ms is not None and contralateral_wave_v_ms is not None:
        interaural_diff = abs(waves.wave_v_ms - contralateral_wave_v_ms)
        if interaural_diff > threshold_ms:
            interaural_flag = True
            flags.append(
                Flag(
                    "interaural_wave_v_exceeded",
                    {
                        "diff_ms": str(interaural_diff),
                        "threshold_ms": str(threshold_ms),
                    },
                )
            )

    return AbrMetricsResult(
        i_iii_ms=i_iii,
        iii_v_ms=iii_v,
        i_v_ms=i_v,
        interaural_v_diff_ms=interaural_diff,
        interaural_v_flag=interaural_flag,
        flags=tuple(flags),
    )


def score(
    waves: AbrWaveInput,
    *,
    contralateral_wave_v_ms: Decimal | None = None,
    threshold_ms: Decimal = DEFAULT_INTERAURAL_V_THRESHOLD_MS,
) -> CalculationResult:
    metrics = compute_abr_metrics(
        waves,
        contralateral_wave_v_ms=contralateral_wave_v_ms,
        threshold_ms=threshold_ms,
    )
    return CalculationResult(
        code=CODE,
        value="true" if metrics.interaural_v_flag else "false",
        unit=None,
        inputs={
            "wave_i_ms": str(waves.wave_i_ms) if waves.wave_i_ms is not None else "",
            "wave_iii_ms": (
                str(waves.wave_iii_ms) if waves.wave_iii_ms is not None else ""
            ),
            "wave_v_ms": str(waves.wave_v_ms) if waves.wave_v_ms is not None else "",
            "threshold_ms": str(threshold_ms),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=metrics.flags,
    )
