import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { testIds } from "@/lib/test/test-id";
import audiologyMessages from "../../../../../../packages/i18n-messages/en/audiology.json";

import { AudiogramWorkspace } from "./AudiogramWorkspace";

const patientId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

const harness = vi.hoisted(() => ({
  save: vi.fn(),
}));

vi.mock("../hooks/use-audiology", () => ({
  useAudiogramCompare: () => ({
    list: {
      data: { items: [], page: { limit: 50, offset: 0, total: 0 } },
      isLoading: false,
      isError: false,
    },
    overlayCandidates: [],
    idempotencyKey: "test-idempotency",
    resetIdempotencyKey: vi.fn(),
  }),
  useSaveAudiogram: () => ({ mutateAsync: harness.save, isPending: false }),
  useFinalizeAudiogram: () => ({ mutateAsync: vi.fn(), isPending: false }),
  usePatientSpeechAudiometry: () => ({ data: { items: [] } }),
  usePatientTympanograms: () => ({ data: { items: [] } }),
  usePatientAbrResults: () => ({ data: { items: [] } }),
  usePatientOaeResults: () => ({ data: { items: [] } }),
  useSaveSpeechAudiometry: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useSaveTympanogram: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useInterpretTympanogram: () => ({ mutateAsync: vi.fn(), isPending: false }),
  usePatientHearingDevices: () => ({ data: { items: [] } }),
  useCreateHearingDevice: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useEvaluateCandidacy: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
    data: undefined,
  }),
  usePediatricAudiologySummary: () => ({
    data: { pediatric: null, omeEpisodes: [] },
    isLoading: false,
    isError: false,
  }),
  useUpdateNewbornScreening: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUpdatePediatricMilestones: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
  useCreateOmeEpisode: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

vi.mock("@/features/clinics", () => ({
  useCurrentClinicQuery: () => ({
    data: { timezone: "UTC" },
    isLoading: false,
  }),
}));

vi.mock("@/features/patients", () => ({
  usePatientQuery: () => ({
    data: { firstName: "Test", lastName: "Patient" },
    isLoading: false,
  }),
}));

vi.mock("@/providers/permission-provider", () => ({
  usePermission: () => true,
}));

vi.mock("@/features/attachments", () => ({
  dateTimeLocalToUtcIso: (value: string) =>
    value.length > 0 ? `${value}:00.000Z` : null,
}));

describe("AudiogramWorkspace", () => {
  afterEach(() => {
    cleanup();
    harness.save.mockReset();
  });

  it("renders chart and grid with ltr direction", async () => {
    harness.save.mockResolvedValue({
      publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB2",
      version: 1,
      status: "draft",
      thresholds: [],
      ptaFormula: null,
      ptaRight: null,
      ptaLeft: null,
      abgRight: null,
      abgLeft: null,
      gradeRight: null,
      gradeLeft: null,
      lossTypeRight: null,
      lossTypeLeft: null,
      configurationRight: null,
      configurationLeft: null,
      asymmetryFlag: false,
      shiftFlag: false,
    });
    const view = render(
      <NextIntlClientProvider
        locale="en"
        messages={{ audiology: audiologyMessages }}
      >
        <AudiogramWorkspace
          patientId={patientId}
          audiogramId={null}
          onAudiogramChange={() => undefined}
        />
      </NextIntlClientProvider>,
    );
    expect(view.getByTestId(testIds.audiology.root)).toBeTruthy();
    fireEvent.click(view.getByTestId(testIds.audiology.viewEntry));
    const charts = view.getAllByTestId(testIds.audiology.chart);
    expect(charts[0]?.getAttribute("dir")).toBe("ltr");
    expect(view.getByTestId(testIds.audiology.grid).getAttribute("dir")).toBe(
      "ltr",
    );
    fireEvent.click(view.getByTestId(testIds.audiology.save));
    await waitFor(() => {
      expect(harness.save).toHaveBeenCalled();
    });
  });
});
