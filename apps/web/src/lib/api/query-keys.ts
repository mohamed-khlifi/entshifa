export const queryKeys = {
  auth: {
    all: ["auth"] as const,
    me: () => [...queryKeys.auth.all, "me"] as const,
    clinics: () => [...queryKeys.auth.all, "clinics"] as const,
  },
  clinics: {
    all: ["clinics"] as const,
    current: () => [...queryKeys.clinics.all, "current"] as const,
    sites: (params?: { offset?: number; limit?: number }) =>
      [...queryKeys.clinics.all, "sites", params ?? {}] as const,
    clinicalSettings: () =>
      [...queryKeys.clinics.all, "clinical-settings"] as const,
  },
  users: {
    all: ["users"] as const,
    list: (params?: { offset?: number; limit?: number; search?: string }) =>
      [...queryKeys.users.all, "list", params ?? {}] as const,
    detail: (publicId: string) =>
      [...queryKeys.users.all, "detail", publicId] as const,
    roles: () => [...queryKeys.users.all, "roles"] as const,
    permissions: () => [...queryKeys.users.all, "permissions"] as const,
  },
} as const;
