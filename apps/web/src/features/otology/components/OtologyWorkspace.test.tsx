import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { svgMarkupForMap } from "@/components/clinical/AnatomicalMap/AnatomicalMap";
import { tympanicMembraneMap } from "@/lib/anatomy/tympanic-membrane.map";
import { testIds } from "@/lib/test/test-id";
import examinationMessages from "../../../../../../packages/i18n-messages/en/examination.json";
import otologyMessages from "../../../../../../packages/i18n-messages/en/otology.json";

import { OtologyWorkspace } from "./OtologyWorkspace";

const patientId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

const harness = vi.hoisted(() => ({
  save: vi.fn(),
}));

vi.mock("../hooks/use-otology", () => ({
  usePatientOtologyExams: () => ({
    data: { items: [], page: { limit: 50, offset: 0, total: 0 } },
    isLoading: false,
    isError: false,
  }),
  usePatientEarDevices: () => ({
    data: { items: [], page: { limit: 50, offset: 0, total: 0 } },
    isLoading: false,
  }),
  useOtologyValueSet: (code: string) => ({
    data: {
      code,
      members:
        code === "tm.canal.findings"
          ? [{ code: "FIND.CANAL.NORMAL", display: "Normal" }]
          : [
              { code: "FIND.TM.NORMAL", display: "Normal" },
              { code: "FIND.TM.CHOLESTEATOMA", display: "Cholesteatoma" },
            ],
    },
    isLoading: false,
  }),
  useSaveOtology: () => ({ mutateAsync: harness.save, isPending: false }),
  useSignOtology: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUpdateEarDevice: () => ({ mutate: vi.fn(), isPending: false }),
  findingMembers: (valueSet: { members?: unknown[] } | undefined) =>
    valueSet?.members ?? [],
}));

vi.mock("@/features/clinics", () => ({
  useCurrentClinicQuery: () => ({ data: { timezone: "UTC" } }),
}));

vi.mock("@/features/attachments", () => ({
  dateTimeLocalToUtcIso: (value: string) =>
    value.length > 0 ? `${value}:00.000Z` : null,
}));

describe("OtologyWorkspace", () => {
  afterEach(() => {
    cleanup();
    harness.save.mockReset();
  });

  it("saves a microscopy exam", async () => {
    harness.save.mockResolvedValue({
      publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB2",
      version: 1,
      procedureId: "01ARZ3NDEKTSV4RRFFQ69G5FB3",
      procedureStatus: "draft",
      procedure: null,
    });
    const view = render(
      <NextIntlClientProvider
        locale="en"
        messages={{
          otology: otologyMessages,
          examination: examinationMessages,
        }}
      >
        <OtologyWorkspace
          patientId={patientId}
          examId={null}
          onExamChange={() => undefined}
        />
      </NextIntlClientProvider>,
    );
    expect(view.getByTestId(testIds.otology.root)).toBeTruthy();
    expect(svgMarkupForMap(tympanicMembraneMap).length).toBeGreaterThan(0);
    fireEvent.click(view.getByTestId(testIds.otology.save));
    await waitFor(() => {
      expect(harness.save).toHaveBeenCalled();
    });
    const input = harness.save.mock.calls[0]?.[0] as {
      examId: string | null;
      createBody: { method: string; patientPublicId: string };
    };
    expect(input.examId).toBeNull();
    expect(input.createBody.method).toBe("microscopy");
    expect(input.createBody.patientPublicId).toBe(patientId);
  });
});
