/** API permission codes (architecture §29). */

export const Permission = {
  ADMIN_USERS: "admin.users",
  ADMIN_CLINIC: "admin.clinic",
  ADMIN_TERMINOLOGY: "admin.terminology",
  AUTH_SESSION_READ: "auth.session.read",
  PATIENT_READ_OWN: "patient.read.own",
  PATIENT_READ_CLINIC: "patient.read.clinic",
  PATIENT_WRITE: "patient.write",
  PATIENT_MERGE: "patient.merge",
} as const;
