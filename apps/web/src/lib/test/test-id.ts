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
    navEndoscopy: testId("patients", "nav-endoscopy"),
    navLaryngoscopy: testId("patients", "nav-laryngoscopy"),
    navPrescriptions: testId("patients", "nav-prescriptions"),
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
    navTimeline: testId("patients", "nav-timeline"),
    timeline: testId("patients", "timeline"),
    timelineType: testId("patients", "timeline-type"),
    timelineLaterality: testId("patients", "timeline-laterality"),
    timelineProblem: testId("patients", "timeline-problem"),
    timelinePrint: testId("patients", "timeline-print"),
    timelineList: testId("patients", "timeline-list"),
    timelineEmpty: testId("patients", "timeline-empty"),
    timelineError: testId("patients", "timeline-error"),
    timelinePrintSheet: testId("patients", "timeline-print-sheet"),
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
    visitBar: testId("documents", "visit-bar"),
    consultation: testId("documents", "consultation"),
    referral: testId("documents", "referral"),
    sickLeave: testId("documents", "sick-leave"),
    certificate: testId("documents", "certificate"),
    imaging: testId("documents", "imaging"),
    laboratory: testId("documents", "laboratory"),
    batch: testId("documents", "batch"),
    imagingForm: testId("documents", "imaging-form"),
    modality: testId("documents", "modality"),
    clinicalQuestion: testId("documents", "clinical-question"),
    renal: testId("documents", "renal"),
    contrast: testId("documents", "contrast"),
    mriWarning: testId("documents", "mri-warning"),
    overrideReason: testId("documents", "override-reason"),
    visitCreate: testId("documents", "visit-create"),
    visitClose: testId("documents", "visit-close"),
    batchList: testId("documents", "batch-list"),
    batchPrint: testId("documents", "batch-print"),
    batchFrame: testId("documents", "batch-frame"),
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
  recalls: {
    nav: testId("recalls", "nav"),
    gate: testId("recalls", "gate"),
    counters: testId("recalls", "counters"),
    counterOverdue: testId("recalls", "counter-overdue"),
    counterUpcoming: testId("recalls", "counter-upcoming"),
    counterUnreachable: testId("recalls", "counter-unreachable"),
    counterActive: testId("recalls", "counter-active"),
    list: testId("recalls", "list"),
    create: testId("recalls", "create"),
    composer: testId("recalls", "composer"),
    reason: testId("recalls", "reason"),
    interval: testId("recalls", "interval"),
    actionType: testId("recalls", "action-type"),
    test: testId("recalls", "test"),
    laterality: testId("recalls", "laterality"),
    window: testId("recalls", "window"),
    bookNow: testId("recalls", "book-now"),
    patientSearch: testId("recalls", "patient-search"),
    doctor: testId("recalls", "doctor"),
    appointmentType: testId("recalls", "appointment-type"),
    site: testId("recalls", "site"),
    startsAt: testId("recalls", "starts-at"),
    room: testId("recalls", "room"),
    submit: testId("recalls", "submit"),
    close: testId("recalls", "close"),
    missing: testId("recalls", "missing"),
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
  prescriptions: {
    root: testId("prescriptions", "root"),
    gate: testId("prescriptions", "gate"),
    loading: testId("prescriptions", "loading"),
    error: testId("prescriptions", "error"),
    empty: testId("prescriptions", "empty"),
    list: testId("prescriptions", "list"),
    encounter: testId("prescriptions", "encounter"),
    needsEncounter: testId("prescriptions", "needs-encounter"),
    builder: testId("prescriptions", "builder"),
    search: testId("prescriptions", "search"),
    searchEmpty: testId("prescriptions", "search-empty"),
    formularyHeading: testId("prescriptions", "formulary-heading"),
    catalogHeading: testId("prescriptions", "catalog-heading"),
    templatesHeading: testId("prescriptions", "templates-heading"),
    freeText: testId("prescriptions", "free-text"),
    freeTextName: testId("prescriptions", "free-text-name"),
    pediatric: testId("prescriptions", "pediatric"),
    weight: testId("prescriptions", "weight"),
    notes: testId("prescriptions", "notes"),
    safety: testId("prescriptions", "safety"),
    saveDraft: testId("prescriptions", "save-draft"),
    issue: testId("prescriptions", "issue"),
    cancel: testId("prescriptions", "cancel"),
    print: testId("prescriptions", "print"),
    paper: testId("prescriptions", "paper"),
    helpers: testId("prescriptions", "helpers"),
    salineVolume: testId("prescriptions", "saline-volume"),
    salineFrequency: testId("prescriptions", "saline-frequency"),
    salineApply: testId("prescriptions", "saline-apply"),
    sprayApply: testId("prescriptions", "spray-apply"),
    dropsApply: testId("prescriptions", "drops-apply"),
    taperStart: testId("prescriptions", "taper-start"),
    taperStep: testId("prescriptions", "taper-step"),
    taperDays: testId("prescriptions", "taper-days"),
    taperFloor: testId("prescriptions", "taper-floor"),
    taperPreview: testId("prescriptions", "taper-preview"),
    taperApply: testId("prescriptions", "taper-apply"),
    taperSchedule: testId("prescriptions", "taper-schedule"),
    dosePreview: testId("prescriptions", "dose-preview"),
    calculateDose: testId("prescriptions", "calculate-dose"),
    templateCode: testId("prescriptions", "template-code"),
    templateSave: testId("prescriptions", "template-save"),
    open: testId("prescriptions", "open"),
    blocked: testId("prescriptions", "blocked"),
  },
  endoscopy: {
    root: testId("endoscopy", "root"),
    loading: testId("endoscopy", "loading"),
    error: testId("endoscopy", "error"),
    empty: testId("endoscopy", "empty"),
    list: testId("endoscopy", "list"),
    newExam: testId("endoscopy", "new"),
    save: testId("endoscopy", "save"),
    sign: testId("endoscopy", "sign"),
    confirmSign: testId("endoscopy", "confirm-sign"),
    cancelSign: testId("endoscopy", "cancel-sign"),
    reload: testId("endoscopy", "reload"),
    conflict: testId("endoscopy", "conflict"),
    validation: testId("endoscopy", "validation"),
    templateNormal: testId("endoscopy", "template", "normal"),
    templatePostFess: testId("endoscopy", "template", "post-fess"),
    templateEpistaxis: testId("endoscopy", "template", "epistaxis"),
    templateHint: testId("endoscopy", "template", "hint"),
    scores: testId("endoscopy", "scores"),
    scorePending: testId("endoscopy", "scores", "pending"),
    comparison: testId("endoscopy", "comparison"),
    comparisonEmpty: testId("endoscopy", "comparison", "empty"),
    trend: testId("endoscopy", "trend"),
    images: testId("endoscopy", "images"),
    imagesEmpty: testId("endoscopy", "images", "empty"),
    imagesUpload: testId("endoscopy", "images", "upload"),
    imagesCapture: testId("endoscopy", "images", "capture"),
    imagesSnap: testId("endoscopy", "images", "snap"),
    imagesStop: testId("endoscopy", "images", "stop"),
    annotate: testId("endoscopy", "annotate"),
    annotateClose: testId("endoscopy", "annotate", "close"),
    annotateSurface: testId("endoscopy", "annotate", "surface"),
    annotateImage: testId("endoscopy", "annotate", "image"),
    toolArrow: testId("endoscopy", "annotate", "arrow"),
    toolCircle: testId("endoscopy", "annotate", "circle"),
    toolLabel: testId("endoscopy", "annotate", "label"),
    toolClear: testId("endoscopy", "annotate", "clear"),
    labelInput: testId("endoscopy", "annotate", "label-input"),
    performedAt: testId("endoscopy", "performed-at"),
    scope: testId("endoscopy", "scope"),
    decongestant: testId("endoscopy", "decongestant"),
    anesthesia: testId("endoscopy", "anesthesia"),
    setting: testId("endoscopy", "setting"),
    laterality: testId("endoscopy", "laterality"),
    tolerance: testId("endoscopy", "tolerance"),
    instrument: testId("endoscopy", "instrument"),
    indication: testId("endoscopy", "indication"),
    conclusion: testId("endoscopy", "conclusion"),
    adenoid: testId("endoscopy", "adenoid"),
    imagesAnnotate: testId("endoscopy", "images", "annotate"),
  },
  laryngoscopy: {
    root: testId("laryngoscopy", "root"),
    loading: testId("laryngoscopy", "loading"),
    error: testId("laryngoscopy", "error"),
    empty: testId("laryngoscopy", "empty"),
    list: testId("laryngoscopy", "list"),
    newExam: testId("laryngoscopy", "new"),
    save: testId("laryngoscopy", "save"),
    sign: testId("laryngoscopy", "sign"),
    confirmSign: testId("laryngoscopy", "confirm-sign"),
    cancelSign: testId("laryngoscopy", "cancel-sign"),
    reload: testId("laryngoscopy", "reload"),
    conflict: testId("laryngoscopy", "conflict"),
    validation: testId("laryngoscopy", "validation"),
    templatePreThyroid: testId("laryngoscopy", "template", "pre-thyroid"),
    templatePostThyroid: testId("laryngoscopy", "template", "post-thyroid"),
    templateParalysis: testId("laryngoscopy", "template", "paralysis"),
    templateFees: testId("laryngoscopy", "template", "fees"),
    templatePediatric: testId("laryngoscopy", "template", "pediatric"),
    templateTracheostomy: testId("laryngoscopy", "template", "tracheostomy"),
    templateHint: testId("laryngoscopy", "template", "hint"),
    scores: testId("laryngoscopy", "scores"),
    scorePending: testId("laryngoscopy", "scores", "pending"),
    comparison: testId("laryngoscopy", "comparison"),
    comparisonEmpty: testId("laryngoscopy", "comparison", "empty"),
    trend: testId("laryngoscopy", "trend"),
    video: testId("laryngoscopy", "video"),
    videoEmpty: testId("laryngoscopy", "video", "empty"),
    videoUpload: testId("laryngoscopy", "video", "upload"),
    videoCapture: testId("laryngoscopy", "video", "capture"),
    videoRecord: testId("laryngoscopy", "video", "record"),
    videoStop: testId("laryngoscopy", "video", "stop"),
    videoCurrent: testId("laryngoscopy", "video", "current"),
    videoPrevious: testId("laryngoscopy", "video", "previous"),
    performedAt: testId("laryngoscopy", "performed-at"),
    scope: testId("laryngoscopy", "scope"),
    anesthesia: testId("laryngoscopy", "anesthesia"),
    setting: testId("laryngoscopy", "setting"),
    laterality: testId("laryngoscopy", "laterality"),
    tolerance: testId("laryngoscopy", "tolerance"),
    instrument: testId("laryngoscopy", "instrument"),
    indication: testId("laryngoscopy", "indication"),
    conclusion: testId("laryngoscopy", "conclusion"),
    mobilityRight: testId("laryngoscopy", "mobility", "right"),
    mobilityLeft: testId("laryngoscopy", "mobility", "left"),
    positionRight: testId("laryngoscopy", "position", "right"),
    positionLeft: testId("laryngoscopy", "position", "left"),
    glottic: testId("laryngoscopy", "glottic"),
    supraglottic: testId("laryngoscopy", "supraglottic"),
    stroboscopyToggle: testId("laryngoscopy", "strobe", "toggle"),
    rfsToggle: testId("laryngoscopy", "rfs", "toggle"),
    grbasToggle: testId("laryngoscopy", "grbas", "toggle"),
    feesToggle: testId("laryngoscopy", "fees", "toggle"),
    pas: testId("laryngoscopy", "fees", "pas"),
    folds: testId("laryngoscopy", "folds"),
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

export function endoscopyExamTestId(publicId: string): string {
  return publicIdTestId("endoscopy.exam", publicId);
}

export function endoscopyStructureTestId(
  code: string,
  laterality: string,
): string {
  return testId("endoscopy", "structure", examinationToken(code), laterality);
}

export function endoscopyStructureControlTestId(
  code: string,
  laterality: string,
  control: "focus" | "status" | "finding",
): string {
  return testId(
    "endoscopy",
    "structure",
    examinationToken(code),
    laterality,
    control,
  );
}

export function endoscopyLkTestId(
  side: "right" | "left",
  item: string,
): string {
  return testId("endoscopy", "lk", side, examinationToken(item));
}

export function endoscopyPolypTestId(side: "right" | "left"): string {
  return testId("endoscopy", "polyp", side);
}

export function endoscopyComparisonTestId(
  code: string,
  laterality: string,
): string {
  return testId("endoscopy", "comparison", examinationToken(code), laterality);
}

export function endoscopyTrendTestId(publicId: string): string {
  return publicIdTestId("endoscopy.trend", publicId);
}

export function laryngoscopyExamTestId(publicId: string): string {
  return publicIdTestId("laryngoscopy.exam", publicId);
}

export function laryngoscopyStructureTestId(
  code: string,
  laterality: string,
): string {
  return testId(
    "laryngoscopy",
    "structure",
    examinationToken(code),
    laterality,
  );
}

export function laryngoscopyStructureControlTestId(
  code: string,
  laterality: string,
  control: "focus" | "status" | "finding",
): string {
  return testId(
    "laryngoscopy",
    "structure",
    examinationToken(code),
    laterality,
    control,
  );
}

export function laryngoscopyComparisonTestId(
  code: string,
  laterality: string,
): string {
  return testId(
    "laryngoscopy",
    "comparison",
    examinationToken(code),
    laterality,
  );
}

export function laryngoscopyTrendTestId(publicId: string): string {
  return publicIdTestId("laryngoscopy.trend", publicId);
}

export function laryngoscopyLesionCellTestId(
  laterality: string,
  third: string,
  surface: string,
): string {
  return testId(
    "laryngoscopy",
    "lesion",
    laterality,
    examinationToken(third),
    examinationToken(surface),
  );
}

export function laryngoscopyRfsTestId(item: string): string {
  return testId("laryngoscopy", "rfs", examinationToken(item));
}

export function laryngoscopyGrbasTestId(item: string): string {
  return testId("laryngoscopy", "grbas", examinationToken(item));
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

export function timelineRowTestId(publicId: string): string {
  return publicIdTestId("patients.timeline.row", publicId);
}

export function recallRowTestId(publicId: string): string {
  return publicIdTestId("recalls.row", publicId);
}

export function recallActionTestId(action: string, publicId: string): string {
  return publicIdTestId(`recalls.action.${action}`, publicId);
}

export function prescriptionRowTestId(publicId: string): string {
  return publicIdTestId("prescriptions.row", publicId);
}

export function prescriptionFormularyTestId(publicId: string): string {
  return publicIdTestId("prescriptions.formulary", publicId);
}

export function prescriptionTemplateTestId(publicId: string): string {
  return publicIdTestId("prescriptions.template", publicId);
}

export function prescriptionAlertTestId(code: string): string {
  const segment = code.replace(/^prescription\./, "").replace(/_/g, "-");
  return testId("prescriptions", "alert", segment);
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
