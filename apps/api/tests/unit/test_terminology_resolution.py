"""Unit tests for locale-aware concept display resolution."""

from __future__ import annotations

from types import SimpleNamespace

from ent.features.terminology.repository import TerminologyRepository


def _concept(code: str = "FIND.TM.PERFORATION") -> SimpleNamespace:
    return SimpleNamespace(code=code)


def _tr(
    *,
    locale: str,
    display: str,
    clinic_id: int | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        locale=locale,
        display=display,
        full_name=display,
        abbreviation=None,
        patient_friendly=None,
        clinic_id=clinic_id,
    )


def test_resolution_prefers_clinic_override_in_requested_locale() -> None:
    repo = TerminologyRepository(session=None, clinic_id=7)  # type: ignore[arg-type]
    resolved = repo.resolve_display(
        concept=_concept(),  # type: ignore[arg-type]
        translations=[  # type: ignore[list-item]
            _tr(locale="fr", display="Perforation", clinic_id=None),
            _tr(locale="fr", display="Perfo (cabinet)", clinic_id=7),
            _tr(locale="en", display="Perforation", clinic_id=None),
        ],
        locale="fr",
        clinic_default_locale="fr",
    )
    assert resolved.display == "Perfo (cabinet)"
    assert resolved.translation_missing is False


def test_resolution_falls_back_to_global_then_clinic_default() -> None:
    repo = TerminologyRepository(session=None, clinic_id=7)  # type: ignore[arg-type]
    resolved = repo.resolve_display(
        concept=_concept(),  # type: ignore[arg-type]
        translations=[  # type: ignore[list-item]
            _tr(locale="en", display="Perforation", clinic_id=None),
            _tr(locale="fr", display="Perforation FR", clinic_id=None),
        ],
        locale="ar",
        clinic_default_locale="fr",
    )
    assert resolved.display == "Perforation FR"
    assert resolved.locale == "fr"


def test_resolution_uses_code_when_no_translation() -> None:
    repo = TerminologyRepository(session=None, clinic_id=7)  # type: ignore[arg-type]
    resolved = repo.resolve_display(
        concept=_concept("FIND.X"),  # type: ignore[arg-type]
        translations=[],
        locale="en",
        clinic_default_locale="fr",
    )
    assert resolved.display == "FIND.X"
    assert resolved.translation_missing is True
