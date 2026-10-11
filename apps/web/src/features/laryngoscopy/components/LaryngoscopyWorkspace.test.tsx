import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { svgMarkupForMap } from "@/components/clinical/AnatomicalMap/AnatomicalMap";
import type {
  LaryngoscopyCreate,
  LaryngoscopyExamRead,
} from "@/lib/api/generated";
import { larynxMap } from "@/lib/anatomy";
import {
  laryngoscopyComparisonTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";
import examinationMessages from "../../../../../../packages/i18n-messages/en/examination.json";
import formsMessages from "../../../../../../packages/i18n-messages/en/forms.json";
import laryngoscopyMessages from "../../../../../../packages/i18n-messages/en/laryngoscopy.json";

import { LaryngoscopyWorkspace } from "./LaryngoscopyWorkspace";

const patientId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
const previousId = "01ARZ3NDEKTSV4RRFFQ69G5FB2";

const harness = vi.hoisted(() => ({
  exams: [] as LaryngoscopyExamRead[],
  save: vi.fn(),
  sign: vi.fn(),
  refetch: vi.fn(),
}));

vi.mock("../hooks/use-laryngoscopy", () => ({
  usePatientLaryngoscopies: () => ({
    data: {
      items: harness.exams,
      page: { limit: 50, offset: 0, total: harness.exams.length },
    },
    isLoading: false,
    isError: false,
    refetch: harness.refetch,
  }),
  useLaryngoscopyValueSet: () => ({
    data: {
      code: "laryngoscopy.findings",
      nameKey: "terminology.valueSet.laryngoscopyFindings",
      locale: "en",
      members: [
        {
          publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB3",
          code: "FIND.LARYNX.NORMAL",
          kind: "finding",
          display: "Normal",
          locale: "en",
          translationMissing: false,
        },
        {
          publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB4",
          code: "FIND.LARYNX.EDEMA",
          kind: "finding",
          display: "Edema",
          locale: "en",
          translationMissing: false,
        },
        {
          publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB5",
          code: "ANAT.LARYNX.VOCAL_FOLD",
          kind: "anatomy",
          display: "Vocal fold",
          locale: "en",
          translationMissing: false,
        },
      ],
    },
    isLoading: false,
  }),
  useSaveLaryngoscopy: () => ({ mutateAsync: harness.save, isPending: false }),
  useSignLaryngoscopy: () => ({ mutateAsync: harness.sign, isPending: false }),
}));

vi.mock("@/features/clinics", () => ({
  useCurrentClinicQuery: () => ({ data: { timezone: "UTC" } }),
}));

vi.mock("@/features/attachments", () => ({
  dateTimeLocalToUtcIso: (value: string) =>
    value.length > 0 ? `${value}:00.000Z` : null,
}));

vi.mock("./LaryngoscopyVideoPanel", () => ({
  LaryngoscopyVideoPanel: () => (
    <video {...testIdProps(testIds.laryngoscopy.videoCurrent)} />
  ),
}));

function previousExam(): LaryngoscopyExamRead {
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
    scopeType: "flexible_fiberoptic",
    vocalFoldRight: { mobility: "immobile", position: "paramedian" },
    vocalFoldLeft: { mobility: "normal", position: null },
    glotticClosure: "posterior_gap",
    supraglotticPattern: null,
    stroboscopyPerformed: false,
    symmetry: null,
    periodicity: null,
    amplitudeRight: null,
    amplitudeLeft: null,
    mucosalWaveRight: null,
    mucosalWaveLeft: null,
    phaseClosure: null,
    phaseSymmetry: null,
    verticalLevel: null,
    nonVibratingSegment: null,
    feesPerformed: false,
    rfsScore: 0,
    refluxFindingScore: null,
    grbas: null,
    pasScore: null,
    consistencies: [],
    residueSites: [],
    structures: [
      {
        bodySite: {
          conceptId: "01ARZ3NDEKTSV4RRFFQ69G5FB5",
          code: "ANAT.LARYNX.VOCAL_FOLD",
          display: "Vocal fold",
        },
        laterality: "right",
        status: "abnormal",
        finding: {
          conceptId: "01ARZ3NDEKTSV4RRFFQ69G5FB4",
          code: "FIND.LARYNX.EDEMA",
          display: "Edema",
        },
      },
    ],
    lesions: [],
    scores: [],
    conclusionText: null,
    createdAt: "2026-01-02T09:00:00.000Z",
    updatedAt: "2026-01-02T09:00:00.000Z",
  };
}

function renderWorkspace() {
  return render(
    <NextIntlClientProvider
      locale="en"
      messages={{
        laryngoscopy: laryngoscopyMessages,
        examination: examinationMessages,
        forms: formsMessages,
      }}
    >
      <LaryngoscopyWorkspace
        patientId={patientId}
        examId={null}
        onExamChange={() => undefined}
      />
    </NextIntlClientProvider>,
  );
}

describe("LaryngoscopyWorkspace", () => {
  beforeEach(() => {
    harness.exams = [previousExam()];
    harness.save.mockReset();
    harness.sign.mockReset();
    harness.save.mockImplementation(
      async (input: { createBody: LaryngoscopyCreate }) => ({
        ...previousExam(),
        publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB6",
        procedureStatus: "draft",
        version: 1,
        vocalFoldRight: input.createBody.vocalFoldRight,
        vocalFoldLeft: input.createBody.vocalFoldLeft,
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
          new Response(svgMarkupForMap(larynxMap), { status: 200 }),
        ),
      ),
    );
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("saves a one-click pre-thyroidectomy check and shows the previous difference", async () => {
    const view = renderWorkspace();
    fireEvent.click(view.getByTestId(testIds.laryngoscopy.templatePreThyroid));
    const changed = view.getByTestId(
      laryngoscopyComparisonTestId("ANAT.LARYNX.VOCAL_FOLD", "right"),
    );
    expect(changed.getAttribute("data-change")).toBe("changed");
    fireEvent.click(view.getByTestId(testIds.laryngoscopy.save));
    await waitFor(() => {
      expect(harness.save).toHaveBeenCalled();
    });
    const input = harness.save.mock.calls[0]?.[0] as {
      createBody: LaryngoscopyCreate;
    };
    expect(input.createBody.vocalFoldRight.mobility).toBe("normal");
    expect(input.createBody.scopeType).toBe("flexible_fiberoptic");
    expect(input.createBody).not.toHaveProperty("rfsScore");
    expect(view.getByTestId(testIds.laryngoscopy.videoCurrent)).toBeTruthy();
  });
});
