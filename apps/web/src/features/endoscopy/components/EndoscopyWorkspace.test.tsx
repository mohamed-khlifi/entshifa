import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { svgMarkupForMap } from "@/components/clinical/AnatomicalMap/AnatomicalMap";
import type { EndoscopyCreate, EndoscopyExamRead } from "@/lib/api/generated";
import { nasalEndoscopyMap } from "@/lib/anatomy";
import { endoscopyComparisonTestId, testIds } from "@/lib/test/test-id";
import endoscopyMessages from "../../../../../../packages/i18n-messages/en/endoscopy.json";
import examinationMessages from "../../../../../../packages/i18n-messages/en/examination.json";
import formsMessages from "../../../../../../packages/i18n-messages/en/forms.json";

import { EndoscopyWorkspace } from "./EndoscopyWorkspace";

const patientId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
const previousId = "01ARZ3NDEKTSV4RRFFQ69G5FB2";

const harness = vi.hoisted(() => ({
  exams: [] as EndoscopyExamRead[],
  save: vi.fn(),
  sign: vi.fn(),
  refetch: vi.fn(),
}));

vi.mock("../hooks/use-endoscopy", () => ({
  usePatientEndoscopies: () => ({
    data: {
      items: harness.exams,
      page: { limit: 50, offset: 0, total: harness.exams.length },
    },
    isLoading: false,
    isError: false,
    refetch: harness.refetch,
  }),
  useEndoscopyValueSet: () => ({
    data: {
      code: "endoscopy.findings",
      nameKey: "terminology.valueSet.endoscopyFindings",
      locale: "en",
      members: [
        {
          publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB3",
          code: "FIND.ENDO.NORMAL",
          kind: "finding",
          display: "Normal",
          locale: "en",
          translationMissing: false,
        },
        {
          publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB4",
          code: "FIND.ENDO.POLYP",
          kind: "finding",
          display: "Polyp",
          locale: "en",
          translationMissing: false,
        },
        {
          publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB5",
          code: "ANAT.NASAL.VESTIBULE",
          kind: "anatomy",
          display: "Vestibule",
          locale: "en",
          translationMissing: false,
        },
      ],
    },
    isLoading: false,
  }),
  useSaveEndoscopy: () => ({ mutateAsync: harness.save, isPending: false }),
  useSignProcedure: () => ({ mutateAsync: harness.sign, isPending: false }),
}));

vi.mock("@/features/clinics", () => ({
  useClinicalSettingsQuery: () => ({
    data: {
      items: [{ key: "polyp_scale", value: "meltzer", source: "system" }],
    },
    isSuccess: true,
  }),
  useCurrentClinicQuery: () => ({ data: { timezone: "UTC" } }),
}));

vi.mock("@/features/attachments", () => ({
  dateTimeLocalToUtcIso: (value: string) =>
    value.length > 0 ? `${value}:00.000Z` : null,
}));

vi.mock("./EndoscopyMediaPanel", () => ({
  EndoscopyMediaPanel: () => null,
}));

function previousExam(): EndoscopyExamRead {
  return {
    publicId: previousId,
    version: 1,
    procedureId: "01ARZ3NDEKTSV4RRFFQ69G5FB1",
    procedureStatus: "signed",
    patientId,
    encounterId: null,
    performedAt: "2026-01-02T09:00:00.000Z",
    laterality: "bilateral",
    anesthesia: "topical_spray",
    setting: "office",
    instrument: null,
    indicationText: null,
    tolerance: "well_tolerated",
    scopeType: "flexible",
    decongestantUsed: false,
    lundKennedyRight: {
      polyps: 2,
      edema: 0,
      discharge: 0,
      scarring: 0,
      crusting: 0,
      total: 2,
    },
    lundKennedyLeft: {
      polyps: 0,
      edema: 0,
      discharge: 0,
      scarring: 0,
      crusting: 0,
      total: 0,
    },
    lundKennedyTotal: 2,
    modifiedLkRight: 2,
    modifiedLkLeft: 0,
    modifiedLkTotal: 2,
    polypGradeRight: 2,
    polypGradeLeft: 0,
    polypScale: "meltzer",
    adenoidObstructionPct: null,
    conclusionText: null,
    structures: [
      {
        bodySite: {
          conceptId: "01ARZ3NDEKTSV4RRFFQ69G5FB5",
          code: "ANAT.NASAL.VESTIBULE",
          display: "Vestibule",
        },
        laterality: "right",
        status: "abnormal",
        finding: {
          conceptId: "01ARZ3NDEKTSV4RRFFQ69G5FB4",
          code: "FIND.ENDO.POLYP",
          display: "Polyp",
        },
      },
    ],
    scores: [],
    createdAt: "2026-01-02T09:00:00.000Z",
    updatedAt: "2026-01-02T09:00:00.000Z",
  };
}

function renderWorkspace() {
  return render(
    <NextIntlClientProvider
      locale="en"
      messages={{
        endoscopy: endoscopyMessages,
        examination: examinationMessages,
        forms: formsMessages,
      }}
    >
      <EndoscopyWorkspace
        patientId={patientId}
        examId={null}
        onExamChange={() => undefined}
      />
    </NextIntlClientProvider>,
  );
}

describe("EndoscopyWorkspace", () => {
  beforeEach(() => {
    harness.exams = [previousExam()];
    harness.save.mockReset();
    harness.sign.mockReset();
    harness.save.mockImplementation(
      async (input: { createBody: EndoscopyCreate }) => ({
        ...previousExam(),
        publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB6",
        procedureStatus: "draft",
        version: 1,
        lundKennedyTotal: 0,
        structures: (input.createBody.structures ?? []).map((row) => ({
          bodySite: {
            conceptId: "01ARZ3NDEKTSV4RRFFQ69G5FB5",
            code: row.bodySiteCode,
            display: row.bodySiteCode,
          },
          laterality: row.laterality,
          status: row.status,
          finding: {
            conceptId: "01ARZ3NDEKTSV4RRFFQ69G5FB3",
            code: row.findingCode,
            display: "Normal",
          },
        })),
      }),
    );
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(svgMarkupForMap(nasalEndoscopyMap), { status: 200 }),
        ),
      ),
    );
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("saves a normal endoscopy from the template and shows the previous difference", async () => {
    const view = renderWorkspace();
    fireEvent.click(view.getByTestId(testIds.endoscopy.templateNormal));
    const changed = view.getByTestId(
      endoscopyComparisonTestId("ANAT.NASAL.VESTIBULE", "right"),
    );
    expect(changed.getAttribute("data-change")).toBe("changed");
    fireEvent.click(view.getByTestId(testIds.endoscopy.save));
    await waitFor(() => {
      expect(harness.save).toHaveBeenCalled();
    });
    const input = harness.save.mock.calls[0]?.[0] as {
      createBody: EndoscopyCreate;
    };
    expect(input.createBody.structures).toHaveLength(27);
    expect(input.createBody.lundKennedyRight.polyps).toBe(0);
    expect(input.createBody).not.toHaveProperty("lundKennedyTotal");
    expect(harness.sign).not.toHaveBeenCalled();
  });
});
