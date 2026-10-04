"""Resolve concept phrases and render an examination narrative."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import ValidationError
from ent.core.security.principal import CurrentUser
from ent.engines.narrative.grammar import NARRATIVE_LOCALES
from ent.engines.narrative.render import render_examination_narrative
from ent.engines.narrative.types import NarrativeFinding
from ent.features.clinics.repository import ClinicRepository
from ent.features.narrative.schemas import (
    NarrativeFindingIn,
    NarrativeRenderRead,
    NarrativeRenderRequest,
)
from ent.features.terminology.models import Concept, ConceptTranslation
from ent.features.terminology.repository import TerminologyRepository

_FALLBACK_LOCALE = "en"


class NarrativeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def render(
        self,
        *,
        user: CurrentUser,
        body: NarrativeRenderRequest,
        content_locale: str,
    ) -> NarrativeRenderRead:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)
        locale = (
            content_locale if content_locale in NARRATIVE_LOCALES else _FALLBACK_LOCALE
        )
        if not body.findings:
            return NarrativeRenderRead(locale=locale, text="")

        repo = TerminologyRepository(self._session, user.clinic_id)
        codes = _codes(body.findings)
        concepts = {row.code: row for row in await repo.list_concepts_by_codes(codes)}
        missing = sorted(code for code in codes if code not in concepts)
        if missing:
            raise ValidationError(reason="unknown_concept", conceptCode=missing[0])

        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        clinic_locale = clinic.default_locale if clinic is not None else locale
        translations = await repo.load_translations_for_concepts(
            [int(concepts[code].id) for code in codes]
        )
        prepared = [
            _finding(
                item,
                concepts,
                repo,
                translations,
                locale=locale,
                clinic_locale=clinic_locale,
            )
            for item in body.findings
        ]
        text = render_examination_narrative(prepared, locale=locale)
        return NarrativeRenderRead(locale=locale, text=text)


def _codes(findings: list[NarrativeFindingIn]) -> list[str]:
    codes: list[str] = []
    seen: set[str] = set()
    for item in findings:
        for code in (item.concept_code, item.body_site_code):
            if code and code not in seen:
                seen.add(code)
                codes.append(code)
    return codes


def _finding(
    item: NarrativeFindingIn,
    concepts: dict[str, Concept],
    repo: TerminologyRepository,
    translations: dict[int, list[ConceptTranslation]],
    *,
    locale: str,
    clinic_locale: str,
) -> NarrativeFinding:
    concept = concepts[item.concept_code]
    body_site = concepts[item.body_site_code] if item.body_site_code else None
    body_label = ""
    if body_site is not None:
        resolved = repo.resolve_display(
            concept=body_site,
            translations=translations.get(int(body_site.id), []),
            locale=locale,
            clinic_default_locale=clinic_locale,
        )
        body_label = resolved.display
    return NarrativeFinding(
        laterality=item.laterality.value,
        status=item.status,
        sort_index=item.sort_index,
        body_site_label=body_label,
        phrase_template=_template(concept, locale),
        concept_code=item.concept_code,
    )


def _template(concept: Concept, locale: str) -> str:
    raw = (concept.properties or {}).get("narrative")
    if not isinstance(raw, dict):
        return "{{bodySite}}"
    preferred = raw.get(locale)
    fallback = raw.get(_FALLBACK_LOCALE)
    if isinstance(preferred, str) and preferred.strip():
        return preferred
    if isinstance(fallback, str) and fallback.strip():
        return fallback
    return "{{bodySite}}"
