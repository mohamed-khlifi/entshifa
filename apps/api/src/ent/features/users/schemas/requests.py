"""User admin request schemas."""

from __future__ import annotations

from pydantic import Field

from ent.core.schemas.base import CamelModel


class UserUpdate(CamelModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    title: str | None = Field(default=None, max_length=40)
    specialty: str | None = Field(default=None, max_length=80)
    license_number: str | None = Field(default=None, max_length=60)
    preferred_locale: str | None = Field(default=None, min_length=2, max_length=10)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    is_active: bool | None = None


class RoleAssignment(CamelModel):
    role_public_id: str = Field(min_length=26, max_length=26)
    site_public_id: str | None = Field(default=None, min_length=26, max_length=26)


class CustomRoleCreate(CamelModel):
    code: str = Field(min_length=2, max_length=40)
    name_key: str = Field(min_length=2, max_length=80)
    permission_codes: list[str] = Field(min_length=1)


class CustomRoleUpdate(CamelModel):
    name_key: str | None = Field(default=None, min_length=2, max_length=80)
    permission_codes: list[str] | None = Field(default=None, min_length=1)


class InvitationCreate(CamelModel):
    email: str = Field(min_length=3, max_length=190)
    role_public_id: str = Field(min_length=26, max_length=26)
    site_public_id: str | None = Field(default=None, min_length=26, max_length=26)


class InvitationAccept(CamelModel):
    token: str = Field(min_length=20, max_length=128)
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)


class PasswordResetRequest(CamelModel):
    email: str = Field(min_length=3, max_length=190)


class PasswordResetConfirm(CamelModel):
    token: str = Field(min_length=20, max_length=128)
    password: str = Field(min_length=8, max_length=128)


class MfaCode(CamelModel):
    code: str = Field(min_length=6, max_length=8)


class MfaDisable(CamelModel):
    password: str = Field(min_length=8, max_length=128)
    code: str = Field(min_length=6, max_length=8)


class MfaLogin(CamelModel):
    mfa_token: str = Field(min_length=20)
    code: str = Field(min_length=6, max_length=8)


class ActiveClinicRequest(CamelModel):
    clinic_public_id: str = Field(min_length=26, max_length=26)
