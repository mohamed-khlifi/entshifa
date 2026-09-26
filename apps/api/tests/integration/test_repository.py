"""Integration tests for BaseRepository tenant scope, pagination, and UnitOfWork."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session_factory
from ent.core.db.unit_of_work import UnitOfWork
from ent.core.events.bus import reset_event_bus
from ent.core.events.events import DomainEvent
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic, Site
from ent.features.clinics.repository import SiteFilter, SiteRepository
from ent.features.clinics.schemas import SiteRead
from tests.support.auth_seed import seed_auth_fixtures


async def _clinic_by_public_id(session: AsyncSession, public_id: str) -> Clinic:
    result = await session.execute(select(Clinic).where(Clinic.public_id == public_id))
    return result.scalar_one()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_site_repository_cannot_return_other_clinic_rows() -> None:
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        clinic_a = await _clinic_by_public_id(session, fixtures["clinic_public_id"])
        clinic_b = await _clinic_by_public_id(
            session, fixtures["other_clinic_public_id"]
        )

        site_a = Site(
            public_id=new_ulid(),
            clinic_id=clinic_a.id,
            name=f"Site A {new_ulid()[:6]}",
            is_primary=True,
        )
        site_b = Site(
            public_id=new_ulid(),
            clinic_id=clinic_b.id,
            name=f"Site B {new_ulid()[:6]}",
            is_primary=True,
        )
        session.add_all([site_a, site_b])
        await session.commit()

        repo_a = SiteRepository(session, clinic_id=clinic_a.id)
        page = await repo_a.list()
        assert all(row.clinic_id == clinic_a.id for row in page.items)
        assert all(row.public_id != site_b.public_id for row in page.items)

        assert await repo_a.get_by_public_id(site_a.public_id) is not None
        assert await repo_a.get_by_public_id(site_b.public_id) is None
        assert await repo_a.get(site_b.id) is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_without_pagination_still_returns_bounded_page() -> None:
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        clinic = await _clinic_by_public_id(session, fixtures["clinic_public_id"])

        sites = [
            Site(
                public_id=new_ulid(),
                clinic_id=clinic.id,
                name=f"Bulk Site {index:03d} {new_ulid()[:4]}",
                is_primary=False,
            )
            for index in range(30)
        ]
        session.add_all(sites)
        await session.commit()

        repo = SiteRepository(session, clinic_id=clinic.id)
        page = await repo.list()
        assert page.limit == 25
        assert len(page.items) == 25
        assert page.total >= 30
        assert page.offset == 0

        schema = page.to_schema(SiteRead)
        dumped = schema.model_dump(by_alias=True)
        assert "items" in dumped
        assert dumped["page"]["limit"] == 25
        assert "isPrimary" in dumped["items"][0]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_site_filter_and_soft_delete_are_tenant_scoped() -> None:
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        clinic_a = await _clinic_by_public_id(session, fixtures["clinic_public_id"])
        clinic_b = await _clinic_by_public_id(
            session, fixtures["other_clinic_public_id"]
        )

        target = Site(
            public_id=new_ulid(),
            clinic_id=clinic_a.id,
            name=f"Filterable {new_ulid()[:6]}",
            city="Lyon",
            is_primary=False,
        )
        other = Site(
            public_id=new_ulid(),
            clinic_id=clinic_b.id,
            name=target.name,
            city="Lyon",
            is_primary=False,
        )
        session.add_all([target, other])
        await session.commit()

        repo = SiteRepository(session, clinic_id=clinic_a.id)
        page = await repo.list(filters=SiteFilter(search="Filterable", city="Lyon"))
        assert len(page.items) == 1
        assert page.items[0].public_id == target.public_id

        await repo.soft_delete(target.id, by_user_id=1)
        await session.commit()
        assert await repo.get(target.id) is None

        # Cross-tenant soft delete must not touch the other clinic's row.
        repo_wrong = SiteRepository(session, clinic_id=clinic_a.id)
        await repo_wrong.soft_delete(other.id, by_user_id=1)
        await session.commit()
        still = await session.get(Site, other.id)
        assert still is not None
        assert still.deleted_at is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unit_of_work_publishes_events_only_after_commit() -> None:
    bus = reset_event_bus()
    factory = get_session_factory()

    async with UnitOfWork(factory, event_bus=bus) as uow:
        fixtures = await seed_auth_fixtures(uow.require_session)
        clinic = await _clinic_by_public_id(
            uow.require_session, fixtures["clinic_public_id"]
        )
        site = Site(
            public_id=new_ulid(),
            clinic_id=clinic.id,
            name=f"UoW Site {new_ulid()[:6]}",
            is_primary=False,
        )
        repo = SiteRepository(uow.require_session, clinic_id=clinic.id)
        await repo.add(site)
        uow.emit(
            DomainEvent(name="site.created", payload={"public_id": site.public_id})
        )

    assert any(event.name == "site.created" for event in bus.published)

    bus.clear_published()
    with pytest.raises(RuntimeError, match="boom"):
        async with UnitOfWork(factory, event_bus=bus) as uow:
            fixtures = await seed_auth_fixtures(uow.require_session)
            clinic = await _clinic_by_public_id(
                uow.require_session,
                fixtures["clinic_public_id"],
            )
            site = Site(
                public_id=new_ulid(),
                clinic_id=clinic.id,
                name=f"Rollback Site {new_ulid()[:6]}",
                is_primary=False,
            )
            await SiteRepository(uow.require_session, clinic_id=clinic.id).add(site)
            uow.emit(
                DomainEvent(name="site.created", payload={"public_id": site.public_id})
            )
            raise RuntimeError("boom")

    assert bus.published == []
