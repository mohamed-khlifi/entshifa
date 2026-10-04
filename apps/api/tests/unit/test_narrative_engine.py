"""Known-answer examination narrative (feature specification §6.8)."""

from __future__ import annotations

import pytest

from ent.engines.narrative.render import (
    VERSION,
    NarrativeLocaleError,
    render_examination_narrative,
)
from ent.engines.narrative.types import NarrativeFinding


def _finding(
    *,
    laterality: str,
    status: str,
    sort_index: int,
    body_site: str,
    template: str,
    code: str = "FIND.X",
) -> NarrativeFinding:
    return NarrativeFinding(
        laterality=laterality,
        status=status,
        sort_index=sort_index,
        body_site_label=body_site,
        phrase_template=template,
        concept_code=code,
    )


def test_version_is_recorded() -> None:
    assert VERSION == "1.0.0"


def test_right_precedes_left_and_not_examined_is_omitted() -> None:
    text = render_examination_narrative(
        [
            _finding(
                laterality="left",
                status="normal",
                sort_index=0,
                body_site="Tympanic membrane",
                template="{{bodySite}}: normal",
                code="FIND.TM.NORMAL",
            ),
            _finding(
                laterality="right",
                status="not_examined",
                sort_index=0,
                body_site="External auditory canal",
                template="{{bodySite}}: normal",
            ),
            _finding(
                laterality="right",
                status="abnormal",
                sort_index=3,
                body_site="Anteroinferior quadrant",
                template="{{bodySite}}: perforation",
                code="FIND.TM.PERFORATION",
            ),
        ],
        locale="en",
    )
    assert text == (
        "Right — Anteroinferior quadrant: perforation. "
        "Left — Tympanic membrane: normal."
    )


def test_positives_precede_grouped_negatives_within_a_side() -> None:
    text = render_examination_narrative(
        [
            _finding(
                laterality="right",
                status="normal",
                sort_index=0,
                body_site="Anterosuperior quadrant",
                template="{{bodySite}}: normal",
            ),
            _finding(
                laterality="right",
                status="normal",
                sort_index=1,
                body_site="External auditory canal",
                template="{{bodySite}}: normal",
            ),
            _finding(
                laterality="right",
                status="abnormal",
                sort_index=2,
                body_site="Anteroinferior quadrant",
                template="{{bodySite}}: perforation",
            ),
        ],
        locale="en",
    )
    assert text == (
        "Right — Anteroinferior quadrant: perforation; "
        "Anterosuperior quadrant: normal and External auditory canal: normal."
    )


def test_french_uses_locale_grammar_and_templates() -> None:
    text = render_examination_narrative(
        [
            _finding(
                laterality="left",
                status="normal",
                sort_index=0,
                body_site="Membrane tympanique",
                template="{{bodySite}} : normal",
            ),
            _finding(
                laterality="right",
                status="abnormal",
                sort_index=1,
                body_site="Quadrant antéro-inférieur",
                template="{{bodySite}} : perforation",
            ),
        ],
        locale="fr",
    )
    assert text == (
        "À droite — Quadrant antéro-inférieur : perforation. "
        "À gauche — Membrane tympanique : normal."
    )


def test_unknown_locale_is_rejected() -> None:
    with pytest.raises(NarrativeLocaleError) as caught:
        render_examination_narrative([], locale="de")
    assert caught.value.locale == "de"
