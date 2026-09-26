"""Integration tests for setting resolution (user → clinic → system)."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.core.errors.exceptions import NotFoundError
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic, Setting
from ent.features.clinics.repository import SettingRepository
from ent.features.clinics.resolver import SettingResolver
from ent.features.users.models import User
from tests.support.auth_seed import seed_auth_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_setting_resolves_user_over_clinic_over_system() -> None:
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        clinic = (
            await session.execute(
                select(Clinic).where(Clinic.public_id == fixtures["clinic_public_id"]),
            )
        ).scalar_one()
        user = (
            await session.execute(
                select(User).where(User.email == fixtures["email"]),
            )
        ).scalar_one()

        repo = SettingRepository(session)
        system = await repo.get_scoped(
            key="pta_formula",
            clinic_id=None,
            user_id=None,
        )
        if system is None:
            session.add(
                Setting(
                    public_id=new_ulid(),
                    clinic_id=None,
                    user_id=None,
                    key="pta_formula",
                    value="4freq_who",
                ),
            )
            await session.flush()

        await repo.upsert_scoped(
            key="pta_formula",
            value="3freq",
            clinic_id=clinic.id,
            user_id=None,
            by_user_id=user.id,
        )
        await repo.upsert_scoped(
            key="pta_formula",
            value="fletcher",
            clinic_id=clinic.id,
            user_id=user.id,
            by_user_id=user.id,
        )
        await session.commit()

        resolver = SettingResolver(session)
        resolved = await resolver.resolve(
            key="pta_formula",
            clinic_id=clinic.id,
            user_id=user.id,
        )
        assert resolved.source == "user"
        assert resolved.value == "fletcher"

        user_row = await repo.get_scoped(
            key="pta_formula",
            clinic_id=clinic.id,
            user_id=user.id,
        )
        assert user_row is not None
        user_row.deleted_at = user_row.created_at
        await session.commit()

        resolved_clinic = await resolver.resolve(
            key="pta_formula",
            clinic_id=clinic.id,
            user_id=user.id,
        )
        assert resolved_clinic.source == "clinic"
        assert resolved_clinic.value == "3freq"

        clinic_row = await repo.get_scoped(
            key="pta_formula",
            clinic_id=clinic.id,
            user_id=None,
        )
        assert clinic_row is not None
        clinic_row.deleted_at = clinic_row.created_at
        await session.commit()

        resolved_system = await resolver.resolve(
            key="pta_formula",
            clinic_id=clinic.id,
            user_id=user.id,
        )
        assert resolved_system.source == "system"
        assert resolved_system.value == "4freq_who"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolver_raises_when_key_missing_everywhere() -> None:
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        clinic = (
            await session.execute(
                select(Clinic).where(Clinic.public_id == fixtures["clinic_public_id"]),
            )
        ).scalar_one()
        user = (
            await session.execute(
                select(User).where(User.email == fixtures["email"]),
            )
        ).scalar_one()

        resolver = SettingResolver(session)
        with pytest.raises(NotFoundError):
            await resolver.resolve(
                key="definitely_missing_setting_key",
                clinic_id=clinic.id,
                user_id=user.id,
            )
