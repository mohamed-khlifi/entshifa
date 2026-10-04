import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { EncounterRead, PatientRead } from "@/lib/api/generated";
import { fieldTestId } from "@/lib/forms/field-test-id";
import { Permission } from "@/lib/permissions";
import {
  encounterComplaintTestId,
  encounterRedFlagTestId,
  testIds,
} from "@/lib/test/test-id";
import { PermissionProvider } from "@/providers/permission-provider";
import encounters from "../../../../../../packages/i18n-messages/en/encounters.json";
import examination from "../../../../../../packages/i18n-messages/en/examination.json";
import patients from "../../../../../../packages/i18n-messages/en/patients.json";

import { ConsultationCockpit } from "./ConsultationCockpit";

const patientId = "01PATIENT00000000000000000";
const encounterId = "01ENCOUNTER000000000000000";

vi.mock("@/lib/i18n/navigation", () => ({
  Link: ({
    children,
    href,
    ...props
  }: {
    children: ReactNode;
    href: string;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("@/providers/session-provider", () => ({
  useSession: () => ({ session: null, isLoading: false }),
}));

vi.mock("@/lib/forms/autosave", () => ({
  readDraftSnapshot: vi.fn(async () => null),
  clearDraftSnapshot: vi.fn(async () => undefined),
  writeDraftSnapshot: vi.fn(async () => undefined),
}));

vi.mock("../hooks/use-encounter-autosave", () => ({
  useEncounterAutosave: () => ({
    status: "idle",
    conflict: null,
    flush: vi.fn(async () => undefined),
  }),
}));

vi.mock("../hooks/use-consultation-session", () => ({
  useConsultationSession: () => ({
    patient: { data: patient(), isLoading: false, isError: false },
    encounters: {
      data: { items: [encounter()] },
      isLoading: false,
      isError: false,
    },
    complaints: {
      data: {
        members: [
          {
            code: "CC.NASAL_OBSTRUCTION",
            publicId: "01NASAL0000000000000000000",
            display: "Nasal obstruction",
          },
          {
            code: "CC.HEARING_LOSS",
            publicId: "01HEARING00000000000000000",
            display: "Hearing loss",
          },
        ],
      },
      isLoading: false,
    },
    active: encounter(),
    needsSite: false,
    createFailed: false,
    loading: false,
    failed: false,
    scope: {
      locale: "en",
      clinicPublicId: "01CLINIC000000000000000000",
      enabled: true,
    },
    recentVisits: [],
  }),
  useTemplateRoute: () => ({
    data: {
      code: "nasal_obstruction",
      config: {
        historyFields: [],
        examSections: [],
        suggestedInstruments: [],
        suggestedTests: [],
        suggestedDocuments: [],
        favoriteDiagnoses: [],
        defaultFollowUpDays: null,
      },
    },
  }),
  useVisitNarrative: () => ({ data: { text: "" } }),
  useCopyVisit: () => ({ isPending: false, mutateAsync: vi.fn() }),
}));

function patient(): PatientRead {
  return {
    publicId: patientId,
    firstName: "Amina",
    lastName: "Benali",
    birthDate: "1990-04-02",
    mrn: "MRN-1",
    flags: [],
    allergies: [],
    problems: [],
    medications: [],
  } as unknown as PatientRead;
}

function encounter(): EncounterRead {
  return {
    addenda: [],
    clinicianPublicId: "01CLINICIAN000000000000000",
    complaints: [],
    encounterType: "consultation",
    patientPublicId: patientId,
    publicId: encounterId,
    signatures: [],
    sitePublicId: "01SITE000000000000000000000",
    startedAt: "2026-10-04T08:00:00.000Z",
    status: "draft",
    version: 1,
  };
}

function renderCockpit() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider
        locale="en"
        messages={{ encounters, examination, patients }}
      >
        <PermissionProvider permissions={[Permission.ENCOUNTER_SIGN]}>
          <ConsultationCockpit
            patientId={patientId}
            encounterId={encounterId}
          />
        </PermissionProvider>
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

describe("ConsultationCockpit", () => {
  afterEach(() => {
    cleanup();
  });

  it("updates the report preview from the complaint, history, and a confirmed red flag", async () => {
    renderCockpit();
    const preview = await screen.findByTestId(testIds.encounters.preview);
    const complaint = screen.getByTestId(
      encounterComplaintTestId("CC.NASAL_OBSTRUCTION"),
    );
    expect(complaint.tagName).toBe("BUTTON");
    complaint.focus();
    expect(document.activeElement).toBe(complaint);
    expect(preview.textContent).not.toContain("Nasal obstruction");

    fireEvent.click(complaint);
    expect(complaint.getAttribute("aria-pressed")).toBe("true");
    expect(preview.textContent).toContain("Nasal obstruction");

    fireEvent.change(screen.getByTestId(fieldTestId("complaintSearch")), {
      target: { value: "no-match" },
    });
    expect(
      screen.queryByTestId(encounterComplaintTestId("CC.NASAL_OBSTRUCTION")),
    ).toBeNull();
    fireEvent.change(screen.getByTestId(fieldTestId("complaintSearch")), {
      target: { value: "" },
    });

    fireEvent.change(screen.getByTestId(fieldTestId("onset")), {
      target: { value: "3 days" },
    });
    await waitFor(() => {
      expect(preview.textContent).toContain("3 days");
    });

    const hearing = screen.getByTestId(
      encounterComplaintTestId("CC.HEARING_LOSS"),
    );
    fireEvent.click(hearing);
    const flag = screen.getByTestId(
      encounterRedFlagTestId("suddenHearingLoss"),
    );
    expect(flag.querySelectorAll("span")).toHaveLength(2);
    fireEvent.click(flag);
    expect(flag.getAttribute("aria-pressed")).toBe("true");
    expect(preview.textContent).toContain("Sudden sensorineural hearing loss");
  }, 20_000);

  it("opens a focusable sign dialog and closes it from the keyboard cancel control", async () => {
    renderCockpit();
    const sign = await screen.findByTestId(testIds.encounters.sign);
    sign.focus();
    expect(document.activeElement).toBe(sign);
    fireEvent.click(sign);
    const dialog = screen.getByTestId(testIds.encounters.signDialog);
    const cancel = screen.getByTestId(testIds.encounters.signCancel);
    cancel.focus();
    expect(document.activeElement).toBe(cancel);
    fireEvent.click(cancel);
    await waitFor(() => {
      expect(dialog.hasAttribute("open")).toBe(false);
    });
  });
});
