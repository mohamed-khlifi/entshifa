"""Own-patient versus clinic-wide read scope.

``patient.read.own`` limits reads to rows this user created. There is no
primary-doctor column until encounters exist (architecture §29 follow-up).
Roles seeded today carry ``patient.read.clinic``, so clinic-wide access is
the default.
"""

from __future__ import annotations

from ent.core.errors.exceptions import PermissionDeniedError
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser


def created_by_scope(user: CurrentUser) -> int | None:
    """Return a creator filter, or None when the user may read the clinic."""

    if Permission.PATIENT_READ_CLINIC.value in user.permissions:
        return None
    if Permission.PATIENT_READ_OWN.value in user.permissions:
        return user.user_id
    raise PermissionDeniedError(permission=Permission.PATIENT_READ_OWN.value)


def assert_patient_visible(user: CurrentUser, created_by_id: int | None) -> None:
    scope = created_by_scope(user)
    if scope is None:
        return
    if created_by_id == scope:
        return
    raise PermissionDeniedError(permission=Permission.PATIENT_READ_CLINIC.value)
