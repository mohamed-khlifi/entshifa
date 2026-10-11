"""MRI request guard for non-MRI-safe implants.

Pure function. No I/O. The feature layer loads flags and records the clinician.
"""

from __future__ import annotations

from dataclasses import dataclass

VERSION = "1.0.0"
REFERENCE = (
    "Feature specification §14.4: an MRI request warns on a pacemaker or "
    "cochlear implant. P2-10 blocks the request unless the ordering clinician "
    "records an override reason. A blank or very short reason does not override."
)

MRI_MODALITIES = frozenset({"mri_iac_gadolinium", "mri_neck"})
NON_MRI_SAFE_IMPLANT_FLAGS = frozenset({"cochlear_implant", "pacemaker"})
MIN_OVERRIDE_REASON_LENGTH = 8


@dataclass(frozen=True, slots=True)
class MriSafetyDecision:
    """Whether this modality may be requested for these flags."""

    blocked: bool
    flags: tuple[str, ...]
    overridden: bool


def evaluate_mri_safety(
    *,
    modality: str,
    flag_codes: tuple[str, ...],
    override_reason: str | None,
) -> MriSafetyDecision:
    """Block MRI when a non-MRI-safe implant is active and no real override exists."""

    if modality not in MRI_MODALITIES:
        return MriSafetyDecision(blocked=False, flags=(), overridden=False)
    hits = tuple(sorted(set(flag_codes) & NON_MRI_SAFE_IMPLANT_FLAGS))
    if not hits:
        return MriSafetyDecision(blocked=False, flags=(), overridden=False)
    reason = (override_reason or "").strip()
    if len(reason) >= MIN_OVERRIDE_REASON_LENGTH:
        return MriSafetyDecision(blocked=False, flags=hits, overridden=True)
    return MriSafetyDecision(blocked=True, flags=hits, overridden=False)


def mentions_contrast_media(labels: tuple[str, ...]) -> bool:
    """True when an allergy display names a contrast agent.

    # VERIFY: clinic terminology may use a coded contrast-media concept later.
    Recognition is assistive. A clinician confirmation is OR-ed by the caller.
    """

    tokens = (
        "contrast",
        "gadolinium",
        "iodine",
        "iode",
        "produit de contraste",
        "غادولينيوم",
        "يود",
    )
    for label in labels:
        folded = label.casefold()
        if any(token.casefold() in folded for token in tokens):
            return True
    return False
