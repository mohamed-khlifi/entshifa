"""Integration tests for terminology seed, search, and locale resolution."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session_factory
from ent.core.security.principal import CurrentUser
from ent.features.clinics.models import Clinic
from ent.features.terminology.models import Concept, ConceptTranslation
from ent.features.terminology.service import TerminologyService
from ent.seeds.terminology import TM_FINDINGS_VALUE_SET, seed_terminology
from tests.support.auth_seed import seed_auth_fixtures


async def _user_for_clinic(session: AsyncSession, clinic_public_id: str) -> CurrentUser:
    clinic = (
        await session.execute(
            select(Clinic).where(Clinic.public_id == clinic_public_id)
        )
    ).scalar_one()
    return CurrentUser(
        user_id=1,
        user_public_id="01USERTESTPUBLICID000000000",
        session_id=1,
        session_public_id="01SESSIONPUBLICID0000000",
        clinic_id=clinic.id,
        clinic_public_id=clinic.public_id,
        permissions=frozenset({"auth.session.read"}),
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_same_concept_renders_in_en_and_fr() -> None:
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        await seed_terminology(session)
        await session.commit()

        user = await _user_for_clinic(session, fixtures["clinic_public_id"])
        service = TerminologyService(session)

        en = await service.get_dictionary(user=user, locale="en", kinds=["finding"])
        fr = await service.get_dictionary(user=user, locale="fr", kinds=["finding"])

        perforation_en = next(
            c for c in en.concepts.values() if c.code == "FIND.TM.PERFORATION"
        )
        perforation_fr = fr.concepts[perforation_en.public_id]
        assert perforation_en.display == "Perforation"
        assert perforation_fr.display == "Perforation"
        assert perforation_en.full_name != perforation_fr.full_name
        assert "tympanic" in (perforation_en.full_name or "").lower()
        assert "tympanique" in (perforation_fr.full_name or "").lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_accented_french_search_with_and_without_accents() -> None:
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        await seed_terminology(session)
        await session.commit()

        user = await _user_for_clinic(session, fixtures["clinic_public_id"])
        service = TerminologyService(session)

        with_accent = await service.search_concepts(
            user=user,
            q="rétraction",
            locale="fr",
            kind="finding",
            limit=25,
            offset=0,
        )
        without_accent = await service.search_concepts(
            user=user,
            q="retraction",
            locale="fr",
            kind="finding",
            limit=25,
            offset=0,
        )
        assert any(item.code == "FIND.TM.RETRACTION" for item in with_accent.items)
        assert any(item.code == "FIND.TM.RETRACTION" for item in without_accent.items)

        # Synonym with accent should also hit perforation.
        synonym = await service.search_concepts(
            user=user,
            q="pérforation",
            locale="fr",
            kind="finding",
            limit=25,
            offset=0,
        )
        assert any(item.code == "FIND.TM.PERFORATION" for item in synonym.items)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_missing_translation_falls_back_to_code_marker() -> None:
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        await seed_terminology(session)
        await session.commit()

        concept = (
            await session.execute(
                select(Concept).where(Concept.code == "FIND.TM.EFFUSION"),
            )
        ).scalar_one()
        # Remove French translation to force missing path for locale=ar default=en.
        fr_rows = (
            (
                await session.execute(
                    select(ConceptTranslation).where(
                        ConceptTranslation.concept_id == concept.id,
                        ConceptTranslation.locale == "fr",
                    ),
                )
            )
            .scalars()
            .all()
        )
        for row in fr_rows:
            await session.delete(row)
        await session.commit()

        # Point clinic default to a locale with no rows (ar) by resolving ar with
        # clinic default also ar — seed clinic default is en, so override via
        # resolve path: request ar, clinic default ar after temporarily patching.
        clinic = (
            await session.execute(
                select(Clinic).where(Clinic.public_id == fixtures["clinic_public_id"]),
            )
        ).scalar_one()
        clinic.default_locale = "ar"
        await session.commit()

        user = await _user_for_clinic(session, fixtures["clinic_public_id"])
        service = TerminologyService(session)
        result = await service.search_concepts(
            user=user,
            q="FIND.TM.EFFUSION",
            locale="ar",
            kind="finding",
            limit=10,
            offset=0,
        )
        # Search by code still finds the concept; display should be missing marker
        # when neither ar nor clinic-default ar translations exist, but en remains
        # — resolution falls to en only if clinic default is en. With default ar
        # and no ar/fr, we get code marker (en is not in the fallback chain unless
        # it is the clinic default).
        match = next(item for item in result.items if item.code == "FIND.TM.EFFUSION")
        assert match.translation_missing is True
        assert match.display == "FIND.TM.EFFUSION"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_value_set_tm_findings() -> None:
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        await seed_terminology(session)
        await session.commit()
        user = await _user_for_clinic(session, fixtures["clinic_public_id"])
        service = TerminologyService(session)
        value_set = await service.get_value_set(
            user=user,
            code=TM_FINDINGS_VALUE_SET,
            locale="en",
        )
        assert value_set.code == TM_FINDINGS_VALUE_SET
        assert len(value_set.members) == 4
        assert any(m.is_default for m in value_set.members)
