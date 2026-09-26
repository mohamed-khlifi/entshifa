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
  uiKit: {
    root: testId("ui-kit", "root"),
    form: testId("ui-kit", "form"),
    formSubmit: testId("ui-kit", "form-submit"),
    table: testId("ui-kit", "table"),
  },
  attachments: {
    viewer: testId("attachments", "viewer"),
    viewerLoad: testId("attachments", "viewer", "load"),
    viewerError: testId("attachments", "viewer", "error"),
    viewerMeta: testId("attachments", "viewer", "meta"),
    viewerImage: testId("attachments", "viewer", "image"),
  },
} as const;

export function publicIdTestId(scope: string, publicId: string): string {
  for (const part of scope.split(".")) {
    assertSegment(part);
  }
  if (!/^[0-9A-HJKMNP-TV-Z]{26}$/.test(publicId)) {
    throw new Error("Invalid public id for test id");
  }
  return `${scope}.${publicId}`;
}
