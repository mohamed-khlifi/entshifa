"""Authentication use cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import (
    AuthenticationError,
    AuthInvalidCredentialsError,
    AuthSessionRevokedError,
    NotFoundError,
)
from ent.core.security.passwords import verify_password
from ent.core.security.throttle import (
    assert_login_allowed,
    clear_login_attempts,
    record_failed_login,
)
from ent.core.security.tokens import (
    create_access_token,
    hash_refresh_token,
    new_refresh_token,
)
from ent.core.utils.ids import new_ulid
from ent.features.auth.repository import AuthRepository
from ent.features.auth.schemas.responses import LoginResponse, SessionResponse
from ent.features.clinics.models import Clinic
from ent.features.users.models import User, UserSession
from ent.settings import Settings


@dataclass(frozen=True, slots=True)
class AuthService:
    session: AsyncSession
    settings: Settings

    def _repo(self) -> AuthRepository:
        return AuthRepository(self.session)

    async def login(
        self,
        *,
        email: str,
        password: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[LoginResponse, str]:
        await assert_login_allowed(email=email, ip_address=ip_address)
        repo = self._repo()
        user = await repo.get_user_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            if user is not None:
                await repo.record_failed_login(user.id)
            await record_failed_login(email=email, ip_address=ip_address)
            raise AuthInvalidCredentialsError()

        clinic = await repo.default_clinic_for_user(user.id)
        if clinic is None:
            raise AuthInvalidCredentialsError()

        now = datetime.now(UTC).replace(tzinfo=None)
        await repo.record_successful_login(user.id, at=now)
        await clear_login_attempts(email=email, ip_address=ip_address)

        raw_refresh = new_refresh_token()
        refresh_hash = hash_refresh_token(raw_refresh)
        family_id = new_ulid()
        expires_at = now + timedelta(days=self.settings.refresh_token_ttl_days)

        session_row = UserSession(
            public_id=new_ulid(),
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            device_label=None,
            ip_address=_encode_ip(ip_address),
            user_agent=user_agent,
            issued_at=now,
            expires_at=expires_at,
            session_family_id=family_id,
            active_clinic_id=clinic.id,
        )
        await repo.create_session(session_row)

        from ent.core.audit.recorder import AuditRecorder
        from ent.core.context import (
            set_clinic_id,
            set_ip_address,
            set_user_agent,
            set_user_id,
        )

        set_user_id(user.id)
        set_clinic_id(clinic.id)
        set_ip_address(ip_address)
        set_user_agent(user_agent)
        AuditRecorder(self.session).record_write(
            action="login",
            entity=session_row,
            before=None,
            after={"session_public_id": session_row.public_id, "user_id": user.id},
            changed_fields=None,
            clinic_id=clinic.id,
        )

        permissions = await repo.load_permission_codes(user.id, clinic.id)
        access_token = create_access_token(
            settings=self.settings,
            user_public_id=user.public_id,
            session_public_id=session_row.public_id,
            clinic_public_id=clinic.public_id,
            permissions=permissions,
        )

        body = LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in_minutes=self.settings.access_token_ttl_minutes,
            session=SessionResponse(
                user_public_id=user.public_id,
                clinic_public_id=clinic.public_id,
                session_public_id=session_row.public_id,
            ),
        )
        return body, raw_refresh

    async def refresh(self, *, raw_refresh_token: str) -> tuple[LoginResponse, str]:
        repo = self._repo()
        token_hash = hash_refresh_token(raw_refresh_token)
        now = datetime.now(UTC).replace(tzinfo=None)

        session_row = await repo.get_session_by_refresh_hash(token_hash)
        if session_row is None:
            replay = await repo.find_replayed_session(token_hash)
            if replay is not None:
                await repo.revoke_session_family(replay.session_family_id, at=now)
                raise AuthSessionRevokedError(reason="refresh_reuse")
            raise AuthenticationError()

        if session_row.expires_at <= now or session_row.revoked_at is not None:
            raise AuthenticationError()

        user = await repo.get_user_by_id(session_row.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError()

        clinic = await repo.get_clinic_by_id(session_row.active_clinic_id)
        if clinic is None:
            raise AuthenticationError()

        new_raw = new_refresh_token()
        new_hash = hash_refresh_token(new_raw)
        await repo.rotate_refresh_token(
            session_row.id,
            previous_hash=token_hash,
            new_hash=new_hash,
        )

        permissions = await repo.load_permission_codes(user.id, clinic.id)
        access_token = create_access_token(
            settings=self.settings,
            user_public_id=user.public_id,
            session_public_id=session_row.public_id,
            clinic_public_id=clinic.public_id,
            permissions=permissions,
        )

        body = LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in_minutes=self.settings.access_token_ttl_minutes,
            session=SessionResponse(
                user_public_id=user.public_id,
                clinic_public_id=clinic.public_id,
                session_public_id=session_row.public_id,
            ),
        )
        return body, new_raw

    async def logout(self, *, raw_refresh_token: str) -> None:
        repo = self._repo()
        token_hash = hash_refresh_token(raw_refresh_token)
        session_row = await repo.get_session_by_refresh_hash(token_hash)
        if session_row is None:
            return
        now = datetime.now(UTC).replace(tzinfo=None)
        await repo.revoke_session(session_row.id, at=now)

    async def get_active_session(self, session_public_id: str) -> UserSession | None:
        repo = self._repo()
        session_row = await repo.get_session_by_public_id(session_public_id)
        if session_row is None or session_row.revoked_at is not None:
            return None
        now = datetime.now(UTC).replace(tzinfo=None)
        if session_row.expires_at <= now:
            return None
        return session_row

    async def get_user_by_public_id(self, public_id: str) -> User | None:
        return await self._repo().get_user_by_public_id(public_id)

    async def get_clinic_by_public_id(self, public_id: str) -> Clinic | None:
        return await self._repo().get_clinic_by_public_id(public_id)

    async def user_belongs_to_clinic(self, user_id: int, clinic_public_id: str) -> bool:
        clinic = await self._repo().get_clinic_by_public_id(clinic_public_id)
        if clinic is None:
            return False
        return await self._repo().user_belongs_to_clinic(user_id, clinic.id)

    async def load_permissions(self, user_id: int, clinic_id: int) -> frozenset[str]:
        return await self._repo().load_permission_codes(user_id, clinic_id)

    async def update_session_active_clinic(
        self, session_id: int, clinic_id: int
    ) -> None:
        await self._repo().update_session_active_clinic(session_id, clinic_id)

    async def assert_clinic_membership_or_not_found(
        self,
        *,
        user_id: int,
        clinic_public_id: str,
    ) -> Clinic:
        clinic = await self._repo().get_clinic_by_public_id(clinic_public_id)
        if clinic is None:
            raise NotFoundError(resource="clinic")
        if not await self._repo().user_belongs_to_clinic(user_id, clinic.id):
            raise NotFoundError(resource="clinic")
        return clinic


def _encode_ip(ip_address: str | None) -> bytes | None:
    if not ip_address:
        return None
    if ":" in ip_address:
        try:
            import ipaddress

            return ipaddress.IPv6Address(ip_address).packed
        except ValueError:
            return None
    try:
        import ipaddress

        return ipaddress.IPv4Address(ip_address).packed
    except ValueError:
        return None
