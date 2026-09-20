"""Security dependency types (see features/auth/dependencies for wiring)."""

from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import get_current_user, require

__all__ = ["CurrentUser", "Permission", "get_current_user", "require"]
