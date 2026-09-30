"""Split a bilateral finding into one row per side (architecture §26)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from ent.engines.observations.types import ObservationDraft

VERSION = "1.0.0"
REFERENCE = (
    "Architecture §26 and feature spec §6: a bilateral finding on a paired "
    "structure is two observations, one per side, so each side can change on "
    "its own. Midline and not-applicable findings stay one row."
)


def expand_bilateral_observations(
    items: Sequence[ObservationDraft],
) -> tuple[ObservationDraft, ...]:
    """Return one draft per stored row. ``bilateral`` becomes right then left."""

    expanded: list[ObservationDraft] = []
    for item in items:
        if item.laterality == "bilateral":
            expanded.append(replace(item, laterality="right"))
            expanded.append(replace(item, laterality="left"))
        else:
            expanded.append(item)
    return tuple(expanded)
