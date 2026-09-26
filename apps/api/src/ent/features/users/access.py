"""Invitations and password reset (P1-02)."""

from __future__ import annotations

import secrets
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.core.security.passwords import hash_password
from ent.core.security.principal import CurrentUser
from ent.core.security.tokens import hash_refresh_token
from ent.core.utils.ids import new_ulid
from ent.features.clinics.repository import SiteRepository
from ent.features.users.models import (
    PasswordResetToken,
    User,
    UserClinicRole,
    UserInvitation,
)
from ent.features.users.repository import UserAdminRepository
from ent.features.users.schemas.requests import (
    InvitationAccept,
    InvitationCreate,
    PasswordResetConfirm,
)
from ent.features.users.schemas.responses import InvitationRead
from ent.integrations.email import send_transactional

_INVITE_DAYS = 7
_RESET_HOURS = 1


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class AccountAccessService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserAdminRepository(session)

    async def create_invitation(
        self, *, actor: CurrentUser, body: InvitationCreate
    ) -> InvitationRead:
        role = await self._repo.get_role(
            clinic_id=actor.clinic_id, public_id=body.role_public_id
        )
        if role is None:
            raise NotFoundError(resource="role", public_id=body.role_public_id)
        site_id = await self._site_id(actor.clinic_id, body.site_public_id)
        raw = secrets.token_urlsafe(32)
        invitation = UserInvitation(
            public_id=new_ulid(),
            clinic_id=actor.clinic_id,
            email=body.email.strip().lower(),
            role_id=role.id,
            site_id=site_id,
            token_hash=hash_refresh_token(raw),
            expires_at=_now() + timedelta(days=_INVITE_DAYS),
            invited_by_id=actor.user_id,
            created_by_id=actor.user_id,
            updated_by_id=actor.user_id,
        )
        self._session.add(invitation)
        await self._session.flush()
        send_transactional(
            to=invitation.email,
            template_code="users.invitation",
            context={"token": raw, "invitationPublicId": invitation.public_id},
        )
        return InvitationRead(
            public_id=invitation.public_id,
            email=invitation.email,
            role_public_id=role.public_id,
        )

    async def accept_invitation(self, body: InvitationAccept) -> None:
        invitation = await self._repo.get_invitation_by_hash(
            hash_refresh_token(body.token)
        )
        if invitation is None or invitation.accepted_at is not None:
            raise NotFoundError(resource="invitation")
        if invitation.expires_at <= _now():
            raise ValidationError(reason="invitation_expired")
        existing = await self._repo.get_user_by_email(invitation.email)
        if existing is None:
            user = User(
                public_id=new_ulid(),
                email=invitation.email,
                password_hash=hash_password(body.password),
                password_changed_at=_now(),
                first_name=body.first_name,
                last_name=body.last_name,
                preferred_locale="en",
                timezone="Europe/Paris",
                email_verified_at=_now(),
            )
            self._session.add(user)
            await self._session.flush()
        else:
            user = existing
        membership = await self._repo.membership(
            clinic_id=invitation.clinic_id,
            user_id=user.id,
            role_id=invitation.role_id,
        )
        if membership is None:
            self._session.add(
                UserClinicRole(
                    public_id=new_ulid(),
                    clinic_id=invitation.clinic_id,
                    user_id=user.id,
                    role_id=invitation.role_id,
                    site_id=invitation.site_id,
                    starts_on=date.today(),
                ),
            )
        else:
            membership.ends_on = None
        invitation.accepted_at = _now()
        await self._session.flush()

    async def request_password_reset(self, email: str) -> None:
        user = await self._repo.get_user_by_email(email.strip().lower())
        if user is None or not user.is_active:
            return
        now = _now()
        await self._repo.invalidate_open_resets(user.id, at=now)
        raw = secrets.token_urlsafe(32)
        self._session.add(
            PasswordResetToken(
                public_id=new_ulid(),
                user_id=user.id,
                token_hash=hash_refresh_token(raw),
                expires_at=now + timedelta(hours=_RESET_HOURS),
            ),
        )
        await self._session.flush()
        send_transactional(
            to=user.email,
            template_code="auth.password_reset",
            context={"token": raw},
        )

    async def confirm_password_reset(self, body: PasswordResetConfirm) -> None:
        row = await self._repo.get_reset_by_hash(hash_refresh_token(body.token))
        if row is None or row.used_at is not None or row.expires_at <= _now():
            raise NotFoundError(resource="password_reset")
        user = await self._session.get(User, row.user_id)
        if user is None or user.deleted_at is not None:
            raise NotFoundError(resource="password_reset")
        user.password_hash = hash_password(body.password)
        user.password_changed_at = _now()
        row.used_at = _now()
        await self._session.flush()

    async def _site_id(self, clinic_id: int, public_id: str | None) -> int | None:
        if public_id is None:
            return None
        site = await SiteRepository(
            self._session, clinic_id=clinic_id
        ).get_by_public_id(public_id)
        if site is None:
            raise NotFoundError(resource="site", public_id=public_id)
        return site.id
