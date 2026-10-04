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
  scheduling: {
    all: ["scheduling"] as const,
    types: () => [...queryKeys.scheduling.all, "types"] as const,
    doctors: () => [...queryKeys.scheduling.all, "doctors"] as const,
    appointments: (filters?: {
      startsAfter?: string;
      startsBefore?: string;
      doctorUserId?: string;
      room?: string;
      siteId?: string;
    }) => [...queryKeys.scheduling.all, "appointments", filters ?? {}] as const,
    waitingRoom: (params?: { on?: string; siteId?: string }) =>
      [...queryKeys.scheduling.all, "waiting-room", params ?? {}] as const,
  },
  documents: {
    all: ["documents"] as const,
    templates: () => [...queryKeys.documents.all, "templates"] as const,
    template: (publicId: string) =>
      [...queryKeys.documents.all, "template", publicId] as const,
    patient: (patientPublicId: string) =>
      [...queryKeys.documents.all, "patient", patientPublicId] as const,
    preview: (publicId: string) =>
      [...queryKeys.documents.all, "preview", publicId] as const,
  },
  attachments: {
    all: ["attachments"] as const,
    list: (filters: {
      patientPublicId: string;
      category?: string;
      laterality?: string;
      capturedFrom?: string;
      capturedTo?: string;
      limit?: number;
      offset?: number;
    }) => [...queryKeys.attachments.all, "list", filters] as const,
    detail: (publicId: string) =>
      [...queryKeys.attachments.all, "detail", publicId] as const,
    download: (publicId: string, variant?: string) =>
      [
        ...queryKeys.attachments.all,
        "download",
        publicId,
        variant ?? "original",
      ] as const,
  },
  examination: {
    all: ["examination"] as const,
    encounters: (patientId: string) =>
      [...queryKeys.examination.all, "encounters", patientId] as const,
    valueSet: (code: string, locale: string) =>
      [...queryKeys.examination.all, "value-set", code, locale] as const,
    narrative: (patientId: string, mapId: string, signature: string) =>
      [
        ...queryKeys.examination.all,
        "narrative",
        patientId,
        mapId,
        signature,
      ] as const,
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
    dictionary: (params: {
      locale: string;
      kinds?: string;
      valueSet?: string;
    }) => [...queryKeys.terminology.all, "dictionary", params] as const,
  },
} as const;
