"""User admin response schemas."""

from __future__ import annotations

from ent.core.schemas.base import CamelModel


class UserRead(CamelModel):
    public_id: str
    email: str
    first_name: str
    last_name: str
    title: str | None
    specialty: str | None
    license_number: str | None
    preferred_locale: str
    timezone: str
    is_active: bool
    mfa_enabled: bool
    role_codes: list[str]


class PermissionRead(CamelModel):
    code: str
    group_code: str


class RoleRead(CamelModel):
    public_id: str
    code: str
    name_key: str
    is_system: bool
    permission_codes: list[str]


class InvitationRead(CamelModel):
    public_id: str
    email: str
    role_public_id: str


class MfaEnrollResponse(CamelModel):
    secret: str
    provisioning_uri: str


class ClinicMembershipRead(CamelModel):
    clinic_public_id: str
    clinic_name: str
    role_codes: list[str]


class ClinicMembershipList(CamelModel):
    items: list[ClinicMembershipRead]
