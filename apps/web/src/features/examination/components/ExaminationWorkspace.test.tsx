import {
  cleanup,
  fireEvent,
  render,
  waitFor,
  within,
} from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { svgMarkupForMap } from "@/components/clinical/AnatomicalMap/AnatomicalMap";
import type {
  EncounterRead,
  ExaminationSnapshotRead,
  NarrativeRenderRequest,
  ObservationBatchCreate,
  ObservationRead,
  PageSchemaExaminationSnapshotRead,
  PageSchemaObservationRead,
  PageSchemaPatientProblemRead,
} from "@/lib/api/generated";
import { anatomicalMaps } from "@/lib/anatomy";
import { regionStorageKey } from "@/lib/anatomy/examination-state";
import {
  examinationFindingTestId,
  examinationMapTestId,
  examinationRegionTestId,
  testIds,
} from "@/lib/test/test-id";
import examinationMessages from "../../../../../../packages/i18n-messages/en/examination.json";

import { ExaminationWorkspace } from "./ExaminationWorkspace";

const patientId = "01PATIENT00000000000000000";
const sourceId = "01SOURCEENCOUNTER0000000000";
const createdId = "01NEWENCOUNTER000000000000";

const harness = vi.hoisted(() => ({
  narrative: null as NarrativeRenderRequest | null,
  encounters: [] as EncounterRead[],
  observations: {
    items: [],
    page: { limit: 100, offset: 0, total: 0 },
  } as PageSchemaObservationRead,
  problems: {
    items: [],
    page: { limit: 100, offset: 0, total: 0 },
  } as PageSchemaPatientProblemRead,
  copyResult: null as {
    encounter: EncounterRead;
    observations: PageSchemaObservationRead;
    snapshots: PageSchemaExaminationSnapshotRead;
  } | null,
  save: vi.fn(),
  copy: vi.fn(),
}));

vi.mock("../hooks/use-examination", () => ({
  usePatientEncounters: () => ({
    data: { items: harness.encounters },
    isLoading: false,
  }),
  useExaminationSites: () => ({ data: { items: [] } }),
  useExaminationValueSets: (codes: readonly string[]) =>
    codes.map(() => ({
      isLoading: false,
      data: {
        members: [{ code: "FIND.CANAL.WAX", display: "Wax" }],
      },
    })),
  useNarrativePreview: (
    _patientId: string,
    _mapId: string,
    body: NarrativeRenderRequest | null,
  ) => {
    harness.narrative = body;
    const findings = body?.findings ?? [];
    const text =
      findings.length === 0
        ? ""
        : findings.every((row) => row.status === "normal")
          ? "Right\nNormal examination"
          : "Right\nWax";
    return { data: { locale: "en", text } };
  },
  useRecordObservations: () => ({ mutate: harness.save, isPending: false }),
  useRecordSnapshot: () => ({ mutate: vi.fn(), isPending: false }),
  useCreateExaminationEncounter: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
  useCopyEncounterForward: () => ({
    mutateAsync: harness.copy,
    isPending: false,
  }),
  useEncounterObservations: () => ({
    data: harness.observations,
    isLoading: false,
    isError: false,
  }),
  useExaminationProblems: () => ({
    data: harness.problems,
    isLoading: false,
    isError: false,
  }),
}));

beforeEach(() => {
  harness.narrative = null;
  harness.encounters = [];
  harness.observations = emptyObservations();
  harness.problems = emptyProblems();
  harness.copyResult = null;
  harness.save.mockReset();
  harness.copy.mockReset();
  harness.copy.mockImplementation(async () => harness.copyResult);
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      const map = anatomicalMaps.find((item) => url.includes(item.svg));
      return Promise.resolve(
        new Response(map ? svgMarkupForMap(map) : "<svg></svg>", {
          status: 200,
        }),
      );
    }),
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ExaminationWorkspace normals", () => {
  it("fills every section from one click and previews the negative findings", async () => {
    const view = renderWorkspace();
    fireEvent.click(view.getByTestId(testIds.examination.normals.all));
    await waitFor(() => {
      expect(
        view
          .getByTestId(examinationRegionTestId("tm.canal"))
          .getAttribute("data-state"),
      ).toBe("normal");
    });
    fireEvent.click(view.getByTestId(testIds.examination.map.lateralityLeft));
    await waitFor(() => {
      expect(
        view
          .getByTestId(examinationRegionTestId("tm.canal"))
          .getAttribute("data-state"),
      ).toBe("normal");
    });
    const findings = harness.narrative?.findings ?? [];
    expect(findings).toHaveLength(54);
    expect(findings.every((row) => row.status === "normal")).toBe(true);
    expect(
      findings.map((row) => `${row.laterality}:${row.mapRegionCode}`),
    ).toEqual(
      expect.arrayContaining([
        "right:tm.canal",
        "left:tm.canal",
        "midline:oral.lips",
      ]),
    );
    const canal = findings.find((row) => row.mapRegionCode === "tm.canal");
    const septum = findings.find((row) => row.mapRegionCode === "nose.septum");
    expect((septum?.sortIndex ?? 0) > (canal?.sortIndex ?? 0)).toBe(true);
    expect(
      within(view.getByTestId(testIds.examination.narrative)).getByText(
        "Normal examination",
      ),
    ).toBeTruthy();
  });

  it("marks one region normal without clearing the others", async () => {
    const view = renderWorkspace();
    fireEvent.click(
      view.getByTestId(testIds.examination.normals.otoscopyRight),
    );
    await waitFor(() => {
      expect(
        view
          .getByTestId(examinationRegionTestId("tm.canal"))
          .getAttribute("data-state"),
      ).toBe("normal");
    });
    fireEvent.click(view.getByTestId(testIds.examination.map.lateralityLeft));
    expect(
      view
        .getByTestId(examinationRegionTestId("tm.canal"))
        .getAttribute("data-state"),
    ).toBe("not_examined");
    fireEvent.click(view.getByTestId(testIds.examination.normals.otoscopyLeft));
    fireEvent.click(view.getByTestId(testIds.examination.normals.rhinoscopy));
    await waitFor(() => {
      const keys = (harness.narrative?.findings ?? []).map(
        (row) => `${row.laterality}:${row.mapRegionCode}`,
      );
      expect(keys).toEqual(
        expect.arrayContaining([
          "right:tm.canal",
          "left:tm.canal",
          "right:nose.vestibule",
          "left:nose.vestibule",
        ]),
      );
      expect(keys).not.toContain("right:oral.tonsil");
    });
  });
});

describe("ExaminationWorkspace copy forward", () => {
  it("prefills history, exam and problems, and keeps an untouched copy unconfirmed", async () => {
    harness.encounters = [signedSource()];
    harness.observations = observationPage();
    harness.problems = problemPage();
    harness.copyResult = {
      encounter: createdEncounter(),
      observations: observationPage(),
      snapshots: emptySnapshots(),
    };
    const view = renderWorkspace();
    fireEvent.click(view.getByTestId(testIds.examination.copyForward.action));
    await waitFor(() => {
      expect(
        view
          .getByTestId(examinationRegionTestId("tm.canal"))
          .getAttribute("data-copied"),
      ).toBe("true");
    });
    const banner = view.getByTestId(testIds.examination.copyForward.banner);
    expect(banner.getAttribute("data-copied")).toBe("true");
    expect(
      within(
        view.getByTestId(testIds.examination.copyForward.history),
      ).getByText("Previous sore throat"),
    ).toBeTruthy();
    expect(
      within(
        view.getByTestId(testIds.examination.copyForward.complaints),
      ).getByText("Otalgia"),
    ).toBeTruthy();
    expect(
      within(
        view.getByTestId(testIds.examination.copyForward.problems),
      ).getByText("Chronic otitis media"),
    ).toBeTruthy();
    expect(
      within(
        view.getByTestId(testIds.examination.copyForward.findingCount),
      ).getByText("1 finding copied."),
    ).toBeTruthy();
    expect(harness.narrative?.findings?.[0]).toMatchObject({
      conceptCode: "FIND.CANAL.WAX",
      laterality: "right",
      status: "abnormal",
    });

    fireEvent.click(view.getByTestId(testIds.examination.save));
    await waitFor(() => {
      expect(harness.save).toHaveBeenCalledTimes(1);
    });
    const first = savedObservations();
    expect(first).toHaveLength(1);
    expect(first[0]).toMatchObject({
      confirmed: false,
      conceptCode: "FIND.CANAL.WAX",
      mapRegionCode: "tm.canal",
      laterality: "right",
      qualifiers: {
        copied: true,
        sourceEncounterPublicId: sourceId,
      },
    });

    fireEvent.click(
      view.getByTestId(testIds.examination.copyForward.confirmAll),
    );
    await waitFor(() => {
      expect(
        view
          .getByTestId(examinationRegionTestId("tm.canal"))
          .getAttribute("data-copied"),
      ).toBe("false");
    });
    expect(banner.getAttribute("data-copied")).toBe("false");
    fireEvent.click(view.getByTestId(testIds.examination.save));
    await waitFor(() => {
      expect(harness.save).toHaveBeenCalledTimes(2);
    });
    const second = savedObservations(1);
    expect(second[0]?.confirmed).toBe(true);
    expect(second[0]?.qualifiers).toBeUndefined();
  });

  it("confirms a single copied region when the clinician edits it", async () => {
    harness.encounters = [signedSource()];
    harness.copyResult = {
      encounter: createdEncounter(),
      observations: observationPage(),
      snapshots: emptySnapshots(),
    };
    const view = renderWorkspace();
    fireEvent.click(view.getByTestId(testIds.examination.copyForward.action));
    const canal = examinationRegionTestId("tm.canal");
    await waitFor(() => {
      expect(view.getByTestId(canal).getAttribute("data-copied")).toBe("true");
    });
    fireEvent.click(view.getByTestId(canal));
    fireEvent.click(
      view.getByTestId(examinationFindingTestId("FIND.CANAL.WAX")),
    );
    await waitFor(() => {
      expect(view.getByTestId(canal).getAttribute("data-copied")).toBe("false");
    });
    fireEvent.click(view.getByTestId(testIds.examination.save));
    await waitFor(() => {
      expect(harness.save).toHaveBeenCalledTimes(1);
    });
    expect(savedObservations()[0]).toMatchObject({
      confirmed: true,
      conceptCode: "FIND.CANAL.WAX",
      status: "abnormal",
    });
    expect(savedObservations()[0]?.qualifiers).toBeUndefined();
  });

  it("uses the previous snapshot when the visit has no map observations", async () => {
    harness.encounters = [signedSource()];
    harness.copyResult = {
      encounter: createdEncounter(),
      observations: emptyObservations(),
      snapshots: {
        items: [
          {
            publicId: "01SNAPSHOT0000000000000000",
            patientPublicId: patientId,
            encounterPublicId: sourceId,
            mapId: anatomicalMaps[1].id,
            laterality: "left",
            version: 1,
            payload: {
              side: "left",
              marks: {
                [regionStorageKey("left", "nose.septum")]: {
                  status: "abnormal",
                  conceptCode: "FIND.NOSE.DEVIATION",
                  dirty: true,
                },
              },
            },
          } as unknown as ExaminationSnapshotRead,
        ],
        page: { limit: 100, offset: 0, total: 1 },
      },
    };
    const view = renderWorkspace();
    fireEvent.click(view.getByTestId(testIds.examination.copyForward.action));
    await waitFor(() => {
      expect(
        view.getByTestId(testIds.examination.copyForward.banner),
      ).toBeTruthy();
    });
    fireEvent.click(
      view.getByTestId(examinationMapTestId(anatomicalMaps[1].id)),
    );
    await waitFor(() => {
      expect(
        view
          .getByTestId(examinationRegionTestId("nose.septum"))
          .getAttribute("data-copied"),
      ).toBe("true");
    });
    fireEvent.click(view.getByTestId(testIds.examination.map.lateralityLeft));
    await waitFor(() => {
      expect(
        view
          .getByTestId(examinationRegionTestId("nose.septum"))
          .getAttribute("data-state"),
      ).toBe("abnormal");
    });
  });
});

function renderWorkspace() {
  return render(
    <NextIntlClientProvider
      locale="en"
      messages={{ examination: examinationMessages }}
    >
      <ExaminationWorkspace patientId={patientId} />
    </NextIntlClientProvider>,
  );
}

function savedObservations(call = 0): ObservationBatchCreate["observations"] {
  const body = harness.save.mock.calls[call]?.[0] as
    ObservationBatchCreate | undefined;
  return body?.observations ?? [];
}

function emptyObservations(): PageSchemaObservationRead {
  return { items: [], page: { limit: 100, offset: 0, total: 0 } };
}

function emptyProblems(): PageSchemaPatientProblemRead {
  return { items: [], page: { limit: 100, offset: 0, total: 0 } };
}

function emptySnapshots(): PageSchemaExaminationSnapshotRead {
  return { items: [], page: { limit: 100, offset: 0, total: 0 } };
}

function observationPage(): PageSchemaObservationRead {
  const row: ObservationRead = {
    publicId: "01OBSERVATION0000000000000",
    patientPublicId: patientId,
    encounterPublicId: sourceId,
    concept: {
      conceptId: "01CONCEPT0000000000000000",
      code: "FIND.CANAL.WAX",
      display: "Wax",
    },
    valueConcept: {
      conceptId: "01CONCEPT0000000000000000",
      code: "FIND.CANAL.WAX",
      display: "Wax",
    },
    mapRegionCode: "tm.canal",
    laterality: "right",
    status: "abnormal",
    valueType: "code",
    effectiveAt: "2026-04-02T08:00:00.000Z",
    source: "clinician",
    components: [],
    version: 1,
  };
  return { items: [row], page: { limit: 100, offset: 0, total: 1 } };
}

function problemPage(): PageSchemaPatientProblemRead {
  return {
    items: [
      {
        publicId: "01PROBLEM00000000000000000",
        diagnosis: {
          conceptId: "01DIAGNOSIS000000000000000",
          code: "DX.OTITIS.CHRONIC",
          display: "Chronic otitis media",
        },
        laterality: "right",
        note: null,
        onsetDate: null,
        resolvedDate: null,
        status: "active",
        version: 1,
      },
    ],
    page: { limit: 100, offset: 0, total: 1 },
  };
}

function signedSource(): EncounterRead {
  return {
    addenda: [],
    clinicianPublicId: "01CLINICIAN000000000000000",
    complaints: [],
    encounterType: "consultation",
    patientPublicId: patientId,
    publicId: sourceId,
    signatures: [],
    sitePublicId: "01SITE000000000000000000000",
    startedAt: "2026-04-02T08:00:00.000Z",
    status: "signed",
    version: 1,
  };
}

function createdEncounter(): EncounterRead {
  return {
    ...signedSource(),
    publicId: createdId,
    status: "draft",
    startedAt: "2026-06-01T09:00:00.000Z",
    previousEncounterPublicId: sourceId,
    historyText: "Previous sore throat",
    chiefComplaintSummary: "Ear pain",
    assessmentText: "Otitis externa",
    planText: "Review in two weeks",
    complaints: [
      {
        publicId: "01COMPLAINT000000000000000",
        concept: {
          conceptId: "01CONCEPT0000000000000000",
          code: "SX.OTALGIA",
          display: "Otalgia",
        },
        isPrimary: true,
        laterality: "right",
        durationText: null,
        sortOrder: 0,
      },
    ],
  };
}
