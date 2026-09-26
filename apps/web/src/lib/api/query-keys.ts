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
  patients: {
    all: ["patients"] as const,
    list: (filters?: {
      search?: string;
      birthDate?: string;
      sex?: string;
      flagCode?: string;
      sort?: string;
      limit?: number;
      offset?: number;
    }) => [...queryKeys.patients.all, "list", filters ?? {}] as const,
    detail: (publicId: string) =>
      [...queryKeys.patients.all, "detail", publicId] as const,
    timeline: (publicId: string) =>
      [...queryKeys.patients.all, "detail", publicId, "timeline"] as const,
  },
  terminology: {
    all: ["terminology"] as const,
    adminConcepts: (params?: { q?: string; limit?: number; offset?: number }) =>
      [...queryKeys.terminology.all, "admin-concepts", params ?? {}] as const,
    valueSets: () => [...queryKeys.terminology.all, "value-sets"] as const,
    valueSet: (code: string) =>
      [...queryKeys.terminology.all, "value-set", code] as const,
    coverage: (locale: string) =>
      [...queryKeys.terminology.all, "coverage", locale] as const,
    search: (params: { q: string; locale: string; kind?: string }) =>
      [...queryKeys.terminology.all, "search", params] as const,
  },
} as const;
