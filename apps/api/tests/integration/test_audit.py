"""Integration tests for audit_log on clinical writes and login."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.audit.hooks import install_audit_listeners
from ent.core.audit.models import AccessLog, AuditLog
from ent.core.context import set_clinic_id, set_request_id, set_user_id
from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Site
from ent.main import create_app
from ent.settings import get_settings
from tests.support.auth_seed import seed_auth_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_site_create_writes_audit_row() -> None:
    install_audit_listeners()
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        await session.commit()

        from ent.features.clinics.models import Clinic

        clinic = (
            await session.execute(
                select(Clinic).where(Clinic.public_id == fixtures["clinic_public_id"]),
            )
        ).scalar_one()

        set_request_id(new_ulid())
        set_user_id(None)
        set_clinic_id(clinic.id)

        site = Site(
            public_id=new_ulid(),
            clinic_id=clinic.id,
            name=f"Audited Site {new_ulid()[:6]}",
            is_primary=False,
        )
        session.add(site)
        await session.flush()
        await session.commit()

        rows = (
            (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.entity_type == "site",
                        AuditLog.entity_public_id == site.public_id,
                    ),
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1
        assert rows[0].action == "create"
        assert rows[0].after_json is not None
        assert rows[0].after_json["name"] == site.name
        assert rows[0].clinic_id == clinic.id
        assert len(rows[0].request_id) == 26


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_writes_audit_and_me_sets_context() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": fixtures["email"], "password": fixtures["password"]},
        )
        assert login.status_code == 200
        token = login.json()["accessToken"]

        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 200
        assert "X-Request-Id" in me.headers

    async with factory() as session:
        login_rows = (
            (
                await session.execute(
                    select(AuditLog).where(AuditLog.action == "login"),
                )
            )
            .scalars()
            .all()
        )
        assert any(row.entity_type == "user_session" for row in login_rows)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_access_log_recorder() -> None:
    from ent.core.audit.recorder import AuditRecorder

    install_audit_listeners()
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        await session.commit()
        from ent.features.clinics.models import Clinic

        clinic = (
            await session.execute(
                select(Clinic).where(Clinic.public_id == fixtures["clinic_public_id"]),
            )
        ).scalar_one()
        set_request_id(new_ulid())
        set_clinic_id(clinic.id)
        set_user_id(None)
        AuditRecorder(session).record_access(
            action="chart_opened",
            entity_type="patient",
            clinic_id=clinic.id,
            entity_public_id=new_ulid(),
        )
        await session.commit()
        rows = (await session.execute(select(AccessLog))).scalars().all()
        assert any(row.action == "chart_opened" for row in rows)
