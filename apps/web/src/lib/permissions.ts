/** API permission codes (architecture §29). */

export const Permission = {
  ADMIN_USERS: "admin.users",
  ADMIN_CLINIC: "admin.clinic",
  ADMIN_TERMINOLOGY: "admin.terminology",
  AUTH_SESSION_READ: "auth.session.read",
} as const;
