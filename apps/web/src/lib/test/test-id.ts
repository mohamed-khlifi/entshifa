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
    header: testId("patients", "header"),
    headerAge: testId("patients", "header-age"),
    headerAllergies: testId("patients", "header-allergies"),
    headerProblems: testId("patients", "header-problems"),
    headerMedications: testId("patients", "header-medications"),
    headerVisits: testId("patients", "header-visits"),
    alertOnlyHearingEar: testId("patients", "alert-only-hearing-ear"),
    alertOther: testId("patients", "alert-other"),
    chart: testId("patients", "chart"),
    conflict: testId("patients", "conflict"),
    conflictReload: testId("patients", "conflict-reload"),
    loading: testId("patients", "loading"),
    error: testId("patients", "error"),
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
