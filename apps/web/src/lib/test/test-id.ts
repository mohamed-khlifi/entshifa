/** Stable `data-testid` factory (architecture §13.7). */

const SEGMENT = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/;

function assertSegment(segment: string): void {
  if (!SEGMENT.test(segment)) {
    throw new Error(`Invalid test id segment: ${segment}`);
  }
}

export function testId(...segments: string[]): string {
  if (segments.length === 0) {
    throw new Error("testId requires at least one segment");
  }
  for (const segment of segments) {
    assertSegment(segment);
  }
  return segments.join(".");
}

export function testIdProps(id: string): { "data-testid": string } {
  return { "data-testid": id };
}

export const testIds = {
  auth: {
    login: {
      root: testId("auth", "login", "root"),
      email: testId("auth", "login", "email"),
      password: testId("auth", "login", "password"),
      submit: testId("auth", "login", "submit"),
      error: testId("auth", "login", "error"),
    },
    mfa: {
      code: testId("auth", "mfa", "code"),
      submit: testId("auth", "mfa", "submit"),
    },
    passwordReset: {
      root: testId("auth", "password-reset", "root"),
      email: testId("auth", "password-reset", "email"),
      submit: testId("auth", "password-reset", "submit"),
      confirmRoot: testId("auth", "password-reset", "confirm-root"),
      password: testId("auth", "password-reset", "password"),
      confirmSubmit: testId("auth", "password-reset", "confirm-submit"),
      link: testId("auth", "password-reset", "link"),
    },
    invite: {
      root: testId("auth", "invite", "root"),
      firstName: testId("auth", "invite", "first-name"),
      lastName: testId("auth", "invite", "last-name"),
      password: testId("auth", "invite", "password"),
      submit: testId("auth", "invite", "submit"),
    },
  },
  layout: {
    shell: testId("layout", "shell"),
    sidebar: testId("layout", "sidebar"),
    topbar: testId("layout", "topbar"),
    main: testId("layout", "main"),
    logout: testId("layout", "logout"),
    homeTitle: testId("layout", "home-title"),
    localeSwitcher: testId("layout", "locale-switcher"),
    localeSwitcherSelect: testId("layout", "locale-switcher-select"),
    clinicSwitcher: testId("layout", "clinic-switcher"),
    clinicSwitcherSelect: testId("layout", "clinic-switcher-select"),
  },
  clinics: {
    profileForm: testId("clinics", "profile-form"),
    profileSave: testId("clinics", "profile-save"),
    logoInput: testId("clinics", "logo-input"),
    logoUpload: testId("clinics", "logo-upload"),
    documentHeader: testId("clinics", "document-header"),
    documentFooter: testId("clinics", "document-footer"),
    sitesTable: testId("clinics", "sites-table"),
    siteCreate: testId("clinics", "site-create"),
    clinicalForm: testId("clinics", "clinical-form"),
    clinicalSave: testId("clinics", "clinical-save"),
  },
  users: {
    table: testId("users", "table"),
    inviteOpen: testId("users", "invite-open"),
    inviteEmail: testId("users", "invite-email"),
    inviteRole: testId("users", "invite-role"),
    inviteSubmit: testId("users", "invite-submit"),
  },
  settings: {
    securityRoot: testId("settings", "security-root"),
    mfaEnroll: testId("settings", "mfa-enroll"),
    mfaQr: testId("settings", "mfa-qr"),
    mfaConfirmCode: testId("settings", "mfa-confirm-code"),
    mfaConfirmSubmit: testId("settings", "mfa-confirm-submit"),
    mfaDisablePassword: testId("settings", "mfa-disable-password"),
    mfaDisableCode: testId("settings", "mfa-disable-code"),
    mfaDisableSubmit: testId("settings", "mfa-disable-submit"),
  },
  forms: {
    autosave: testId("forms", "autosave"),
    dirtyGuard: testId("forms", "dirty-guard"),
  },
  data: {
    table: testId("data", "table"),
    empty: testId("data", "empty"),
    filterBar: testId("data", "filter-bar"),
    filterInput: testId("data", "filter-input"),
    pagination: testId("data", "pagination"),
    pageSize: testId("data", "page-size"),
    pagePrev: testId("data", "page-prev"),
    pageNext: testId("data", "page-next"),
    columnVisibility: testId("data", "column-visibility"),
  },
  attachments: {
    viewer: testId("attachments", "viewer"),
    viewerLoad: testId("attachments", "viewer", "load"),
    viewerError: testId("attachments", "viewer", "error"),
    viewerMeta: testId("attachments", "viewer", "meta"),
    viewerImage: testId("attachments", "viewer", "image"),
    viewerClose: testId("attachments", "viewer", "close"),
    gallery: testId("attachments", "gallery"),
    galleryLoading: testId("attachments", "gallery", "loading"),
    galleryEmpty: testId("attachments", "gallery", "empty"),
    galleryError: testId("attachments", "gallery", "error"),
    filterCategory: testId("attachments", "filter", "category"),
    filterLaterality: testId("attachments", "filter", "laterality"),
    filterFrom: testId("attachments", "filter", "from"),
    filterTo: testId("attachments", "filter", "to"),
    uploadOpen: testId("attachments", "upload", "open"),
    uploadPanel: testId("attachments", "upload", "panel"),
    uploadFile: testId("attachments", "upload", "file"),
    uploadCategory: testId("attachments", "upload", "category"),
    uploadLaterality: testId("attachments", "upload", "laterality"),
    uploadCapturedAt: testId("attachments", "upload", "captured-at"),
    uploadCaption: testId("attachments", "upload", "caption"),
    uploadConsent: testId("attachments", "upload", "consent"),
    uploadSubmit: testId("attachments", "upload", "submit"),
    uploadProgress: testId("attachments", "upload", "progress"),
    uploadRetry: testId("attachments", "upload", "retry"),
    uploadError: testId("attachments", "upload", "error"),
    bodySite: testId("attachments", "body-site"),
    bodySiteClear: testId("attachments", "body-site", "clear"),
    bodySiteResults: testId("attachments", "body-site", "results"),
    pagePrev: testId("attachments", "page", "prev"),
    pageNext: testId("attachments", "page", "next"),
    forbidden: testId("attachments", "forbidden"),
  },
  patients: {
    nav: testId("patients", "nav"),
    gate: testId("patients", "gate"),
    list: testId("patients", "list"),
    create: testId("patients", "create"),
    createForm: testId("patients", "create-form"),
    createSubmit: testId("patients", "create-submit"),
    editForm: testId("patients", "edit-form"),
    duplicate: testId("patients", "duplicate"),
    duplicateConfirm: testId("patients", "duplicate-confirm"),
    duplicateCancel: testId("patients", "duplicate-cancel"),
    filterSex: testId("patients", "filter-sex"),
    filterBirthDate: testId("patients", "filter-birth-date"),
    filterFlag: testId("patients", "filter-flag"),
    shell: testId("patients", "shell"),
    chartNav: testId("patients", "chart-nav"),
    navOverview: testId("patients", "nav-overview"),
    navExamination: testId("patients", "nav-examination"),
    navConsultation: testId("patients", "nav-consultation"),
    navAttachments: testId("patients", "nav-attachments"),
    header: testId("patients", "header"),
    headerAge: testId("patients", "header-age"),
    headerAllergies: testId("patients", "header-allergies"),
    headerProblems: testId("patients", "header-problems"),
    headerMedications: testId("patients", "header-medications"),
    headerVisits: testId("patients", "header-visits"),
    alertOnlyHearingEar: testId("patients", "alert-only-hearing-ear"),
    alertOther: testId("patients", "alert-other"),
    chart: testId("patients", "chart"),
    problemsActive: testId("patients", "chart", "problems-active"),
    problemsResolved: testId("patients", "chart", "problems-resolved"),
    chartRemove: (section: string, publicId: string) =>
      publicIdTestId(`patients.chart.${section}.remove`, publicId),
    conflict: testId("patients", "conflict"),
    conflictReload: testId("patients", "conflict-reload"),
    loading: testId("patients", "loading"),
    error: testId("patients", "error"),
  },
  documents: {
    nav: testId("documents", "nav"),
    patientNav: testId("documents", "patient-nav"),
    gate: testId("documents", "gate"),
    list: testId("documents", "list"),
    create: testId("documents", "create"),
    templateSelect: testId("documents", "template-select"),
    localeSelect: testId("documents", "locale-select"),
    preview: testId("documents", "preview"),
    previewFrame: testId("documents", "preview-frame"),
    finalize: testId("documents", "finalize"),
    download: testId("documents", "download"),
    print: testId("documents", "print"),
    editor: testId("documents", "editor"),
    editorLocale: testId("documents", "editor-locale"),
    editorBody: testId("documents", "editor-body"),
    editorHeader: testId("documents", "editor-header"),
    editorFooter: testId("documents", "editor-footer"),
    editorCss: testId("documents", "editor-css"),
    editorSave: testId("documents", "editor-save"),
    editorPreview: testId("documents", "editor-preview"),
    placeholder: testId("documents", "placeholder"),
    copy: testId("documents", "copy"),
    signatureInput: testId("documents", "signature-input"),
  },
  scheduling: {
    nav: testId("scheduling", "nav"),
    gate: testId("scheduling", "gate"),
    prev: testId("scheduling", "prev"),
    next: testId("scheduling", "next"),
    today: testId("scheduling", "today"),
    viewDay: testId("scheduling", "view-day"),
    viewWeek: testId("scheduling", "view-week"),
    doctorFilter: testId("scheduling", "doctor-filter"),
    roomFilter: testId("scheduling", "room-filter"),
    bookOpen: testId("scheduling", "book-open"),
    calendar: testId("scheduling", "calendar"),
    calendarLoading: testId("scheduling", "calendar-loading"),
    calendarEmpty: testId("scheduling", "calendar-empty"),
    selectedActions: testId("scheduling", "selected-actions"),
    arrive: testId("scheduling", "arrive"),
    inRoom: testId("scheduling", "in-room"),
    complete: testId("scheduling", "complete"),
    noShow: testId("scheduling", "no-show"),
    cancel: testId("scheduling", "cancel"),
    waitingRoom: testId("scheduling", "waiting-room"),
    waitingEmpty: testId("scheduling", "waiting-empty"),
    bookForm: testId("scheduling", "book-form"),
    bookPatientSearch: testId("scheduling", "book-patient-search"),
    bookDoctor: testId("scheduling", "book-doctor"),
    bookType: testId("scheduling", "book-type"),
    bookSite: testId("scheduling", "book-site"),
    bookStart: testId("scheduling", "book-start"),
    bookDuration: testId("scheduling", "book-duration"),
    bookRoom: testId("scheduling", "book-room"),
    bookSubmit: testId("scheduling", "book-submit"),
    bookCancel: testId("scheduling", "book-cancel"),
    appointmentRow: (publicId: string) =>
      publicIdTestId("scheduling.appointment", publicId),
    waitingRow: (publicId: string) =>
      publicIdTestId("scheduling.waiting", publicId),
  },
  examination: {
    root: testId("examination", "root"),
    mapSelect: testId("examination", "map-select"),
    encounter: testId("examination", "encounter"),
    encounterEmpty: testId("examination", "encounter-empty"),
    save: testId("examination", "save"),
    snapshot: testId("examination", "snapshot"),
    narrative: testId("examination", "narrative"),
    normals: {
      group: testId("examination", "normals"),
      all: testId("examination", "normal-all"),
      otoscopyRight: testId("examination", "normal-otoscopy-right"),
      otoscopyLeft: testId("examination", "normal-otoscopy-left"),
      rhinoscopy: testId("examination", "normal-rhinoscopy"),
      oral: testId("examination", "normal-oral"),
      neck: testId("examination", "normal-neck"),
    },
    copyForward: {
      action: testId("examination", "copy-forward"),
      unavailable: testId("examination", "copy-forward-unavailable"),
      banner: testId("examination", "copy-banner"),
      confirmAll: testId("examination", "confirm-all-copied"),
      history: testId("examination", "copy-history"),
      complaints: testId("examination", "copy-complaints"),
      problems: testId("examination", "copy-problems"),
      findingCount: testId("examination", "copy-finding-count"),
    },
    map: {
      root: testId("examination", "map", "root"),
      lateralityRight: testId("examination", "map", "laterality-right"),
      lateralityLeft: testId("examination", "map", "laterality-left"),
      findingPicker: testId("examination", "map", "finding-picker"),
      notExamined: testId("examination", "map", "not-examined"),
      copiedBadge: testId("examination", "map", "copied-badge"),
    },
  },
  encounters: {
    root: testId("encounters", "root"),
    loading: testId("encounters", "loading"),
    error: testId("encounters", "error"),
    needsSite: testId("encounters", "needs-site"),
    patientCard: testId("encounters", "patient-card"),
    visits: testId("encounters", "visits"),
    questionnaire: testId("encounters", "questionnaire"),
    complaints: testId("encounters", "complaints"),
    complaintSearch: testId("encounters", "complaint-search"),
    history: testId("encounters", "history"),
    redFlags: testId("encounters", "red-flags"),
    suggestions: testId("encounters", "suggestions"),
    exam: testId("encounters", "exam"),
    assessment: testId("encounters", "assessment"),
    plan: testId("encounters", "plan"),
    planAdd: testId("encounters", "plan-add"),
    preview: testId("encounters", "preview"),
    bottomBar: testId("encounters", "bottom-bar"),
    print: testId("encounters", "print"),
    sign: testId("encounters", "sign"),
    signDialog: testId("encounters", "sign-dialog"),
    signConfirm: testId("encounters", "sign-confirm"),
    signCancel: testId("encounters", "sign-cancel"),
    conflict: testId("encounters", "conflict"),
    conflictReload: testId("encounters", "conflict-reload"),
    addendum: testId("encounters", "addendum"),
    addendumSubmit: testId("encounters", "addendum-submit"),
    followUp: testId("encounters", "follow-up"),
    signed: testId("encounters", "signed"),
  },
  terminology: {
    concepts: {
      root: testId("terminology", "concepts", "root"),
      createOpen: testId("terminology", "concepts", "create-open"),
      code: testId("terminology", "concepts", "code"),
      display: testId("terminology", "concepts", "display"),
      createSubmit: testId("terminology", "concepts", "create-submit"),
      select: testId("terminology", "concepts", "select"),
      override: testId("terminology", "concepts", "override"),
      renameSubmit: testId("terminology", "concepts", "rename-submit"),
    },
    valueSets: {
      root: testId("terminology", "value-sets", "root"),
      select: testId("terminology", "value-sets", "select"),
      conceptId: testId("terminology", "value-sets", "concept-id"),
      add: testId("terminology", "value-sets", "add"),
    },
    coverage: {
      root: testId("terminology", "coverage", "root"),
      locale: testId("terminology", "coverage", "locale"),
    },
  },
} as const;

export function examinationMapTestId(mapId: string): string {
  return testId("examination", "map-select", examinationToken(mapId));
}

export function examinationRegionTestId(regionId: string): string {
  return testId("examination", "map", "region", examinationToken(regionId));
}

export function examinationFindingTestId(conceptCode: string): string {
  return testId("examination", "map", "finding", examinationToken(conceptCode));
}

export function examinationRegionConfirmTestId(regionId: string): string {
  return testId("examination", "map", "confirm", examinationToken(regionId));
}

function examinationToken(value: string): string {
  const segment = value.toLowerCase().replaceAll("_", "-").replaceAll(".", "-");
  assertSegment(segment);
  return segment;
}

export function encounterComplaintTestId(code: string): string {
  return testId("encounters", "complaint", examinationToken(code));
}

export function encounterMakePrimaryTestId(code: string): string {
  return testId("encounters", "make-primary", examinationToken(code));
}

export function encounterRedFlagTestId(flagId: string): string {
  return testId("encounters", "red-flag", examinationToken(flagId));
}

export function encounterRegionTestId(region: string): string {
  return testId("encounters", "region", examinationToken(region));
}

export function encounterSuggestionTestId(kind: string, code: string): string {
  return testId(
    "encounters",
    "suggestion",
    examinationToken(kind),
    examinationToken(code),
  );
}

export function encounterMapToggleTestId(mapId: string): string {
  return testId("encounters", "map", examinationToken(mapId));
}

export function encounterVisitTestId(publicId: string): string {
  return publicIdTestId("encounters.visit", publicId);
}

export function diagnosisRowTestId(
  conceptPublicId: string,
  laterality: string,
): string {
  return `${publicIdTestId("encounters.diagnosis", conceptPublicId)}.${laterality}`;
}

export function diagnosisSaveFavoriteTestId(
  conceptPublicId: string,
  laterality: string,
): string {
  return `${diagnosisRowTestId(conceptPublicId, laterality)}.save-favorite`;
}

export function diagnosisFavoriteTestId(conceptPublicId: string): string {
  return publicIdTestId("encounters.diagnosis.favorite", conceptPublicId);
}

export function patientRowTestId(publicId: string): string {
  return publicIdTestId("patients.list.row", publicId);
}

export function publicIdTestId(scope: string, publicId: string): string {
  for (const part of scope.split(".")) {
    assertSegment(part);
  }
  if (!/^[0-9A-HJKMNP-TV-Z]{26}$/.test(publicId)) {
    throw new Error("Invalid public id for test id");
  }
  return `${scope}.${publicId}`;
}
