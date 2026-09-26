"""API tests for users, roles, invitations, reset, MFA and clinic switch."""

from __future__ import annotations

import pyotp
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.features.users.models import User
from ent.integrations.email import get_email_outbox
from ent.main import create_app
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["accessToken"]
    assert token
    return str(token)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_users_roles_invite_reset_and_permission_change() -> None:
    from ent.core.db.session import get_session_factory

    app = create_app(settings=get_settings())
    factory = get_session_factory()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await session.commit()
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

    get_email_outbox().clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await _login(client, fixtures["admin_email"], fixtures["password"])
        headers = {"Authorization": f"Bearer {admin}"}

        doctor = await _login(client, fixtures["doctor_email"], fixtures["password"])
        forbidden = await client.post(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {doctor}"},
            json={
                "code": "nope",
                "nameKey": "role.custom",
                "permissionCodes": ["auth.session.read"],
            },
        )
        assert forbidden.status_code == 403

        suffix = new_ulid()[:8].lower()
        scribe_email = f"scribe+{suffix}@test.entshifa.local"
        created = await client.post(
            "/api/v1/roles",
            headers=headers,
            json={
                "code": f"scribe{suffix}",
                "nameKey": "role.scribe",
                "permissionCodes": ["auth.session.read"],
            },
        )
        assert created.status_code == 201
        role_id = created.json()["publicId"]

        invited = await client.post(
            "/api/v1/invitations",
            headers=headers,
            json={
                "email": scribe_email,
                "rolePublicId": role_id,
            },
        )
        assert invited.status_code == 201
        token = get_email_outbox().messages[-1].context["token"]
        accept = await client.post(
            "/api/v1/auth/invitations/accept",
            json={
                "token": token,
                "password": "ScribePass1!",
                "firstName": "Sam",
                "lastName": "Scribe",
            },
        )
        assert accept.status_code == 204

        scribe = await _login(client, scribe_email, "ScribePass1!")
        denied = await client.get(
            "/api/v1/auth/admin-check",
            headers={"Authorization": f"Bearer {scribe}"},
        )
        assert denied.status_code == 403

        updated = await client.patch(
            f"/api/v1/roles/{role_id}",
            headers=headers,
            json={"permissionCodes": ["auth.session.read", "admin.users"]},
        )
        assert updated.status_code == 200

        allowed = await client.get(
            "/api/v1/auth/admin-check",
            headers={"Authorization": f"Bearer {scribe}"},
        )
        assert allowed.status_code == 204

        other_user = await client.get(
            "/api/v1/users/01ARZ3NDEKTSV4RRFFQ69G5FAV",
            headers=headers,
        )
        assert other_user.status_code == 404

        get_email_outbox().clear()
        reset = await client.post(
            "/api/v1/auth/password-reset",
            json={"email": scribe_email},
        )
        assert reset.status_code == 204
        reset_token = get_email_outbox().messages[-1].context["token"]
        confirm = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": reset_token, "password": "ScribePass2!"},
        )
        assert confirm.status_code == 204
        await _login(client, scribe_email, "ScribePass2!")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_clinic_switch_changes_scope() -> None:
    from ent.core.db.session import get_session_factory
    from ent.seeds.identity import ensure_role, ensure_user_with_role

    app = create_app(settings=get_settings())
    factory = get_session_factory()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            other = (
                await session.execute(
                    select(Clinic).where(
                        Clinic.public_id == fixtures["other_clinic_public_id"]
                    ),
                )
            ).scalar_one()
            role = await ensure_role(
                session, clinic=other, code="doctor", name_key="role.doctor"
            )
            doctor = (
                await session.execute(
                    select(User).where(User.email == fixtures["doctor_email"]),
                )
            ).scalar_one()
            await ensure_user_with_role(
                session,
                clinic=other,
                role=role,
                email=doctor.email,
                first_name=doctor.first_name,
                last_name=doctor.last_name,
            )
            await session.commit()
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client, fixtures["doctor_email"], fixtures["password"])
        headers = {"Authorization": f"Bearer {token}"}
        current = await client.get("/api/v1/clinic", headers=headers)
        assert current.json()["publicId"] == fixtures["clinic_public_id"]

        switched = await client.post(
            "/api/v1/auth/active-clinic",
            headers=headers,
            json={"clinicPublicId": fixtures["other_clinic_public_id"]},
        )
        assert switched.status_code == 200
        new_token = switched.json()["accessToken"]
        scoped = await client.get(
            "/api/v1/clinic",
            headers={"Authorization": f"Bearer {new_token}"},
        )
        assert scoped.status_code == 200
        assert scoped.json()["publicId"] == fixtures["other_clinic_public_id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_optional_totp_login() -> None:
    app = create_app(settings=get_settings())
    factory_import = __import__("ent.core.db.session", fromlist=["get_session_factory"])
    factory = factory_import.get_session_factory()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await session.commit()
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client, fixtures["doctor_email"], fixtures["password"])
        headers = {"Authorization": f"Bearer {token}"}
        enroll = await client.post("/api/v1/auth/mfa/enroll", headers=headers)
        assert enroll.status_code == 200
        secret = enroll.json()["secret"]
        code = pyotp.TOTP(secret).now()
        confirm = await client.post(
            "/api/v1/auth/mfa/confirm",
            headers=headers,
            json={"code": code},
        )
        assert confirm.status_code == 204

        challenged = await client.post(
            "/api/v1/auth/login",
            json={
                "email": fixtures["doctor_email"],
                "password": fixtures["password"],
            },
        )
        assert challenged.status_code == 200
        body = challenged.json()
        assert body["mfaRequired"] is True
        assert body["accessToken"] is None
        done = await client.post(
            "/api/v1/auth/mfa",
            json={"mfaToken": body["mfaToken"], "code": pyotp.TOTP(secret).now()},
        )
        assert done.status_code == 200
        assert done.json()["accessToken"]
