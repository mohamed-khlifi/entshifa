import { cleanup, render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { testIds } from "@/lib/test/test-id";
import audiologyMessages from "../../../../../../packages/i18n-messages/en/audiology.json";

import { AudiologyDashboard } from "./AudiologyDashboard";

vi.mock("../hooks/use-audiology", () => ({
  usePatientSpeechAudiometry: () => ({ data: { items: [] } }),
  usePatientTympanograms: () => ({ data: { items: [] } }),
  usePatientAbrResults: () => ({ data: { items: [] } }),
  useSaveSpeechAudiometry: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useSaveTympanogram: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useInterpretTympanogram: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

const audiogram = {
  publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB2",
  performedAt: "2024-06-01T10:00:00Z",
  thresholds: [],
  abgLeft: null,
  abgRight: 5,
  asymmetryFlag: true,
  baselineAudiogramPublicId: null,
  calibrationDate: null,
  configurationLeft: "flat",
  configurationRight: "sloping",
  encounterPublicId: null,
  engineVersion: "1",
  equipment: null,
  gradeLeft: "mild",
  gradeRight: "moderate",
  hasExtendedHighFrequencies: false,
  interpretationText: "Stable vs baseline.",
  isBaseline: false,
  isMinimumResponseLevel: false,
  isBinauralSoundfield: false,
  lossTypeLeft: "sensorineural",
  lossTypeRight: "mixed",
  method: "standard" as const,
  patientPublicId: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  performedByPublicId: "01ARZ3NDEKTSV4RRFFQ69G5FB0",
  ptaFormula: "4freq_who",
  ptaLeft: 25,
  ptaRight: 40,
  reliability: "good" as const,
  shiftFlag: false,
  status: "final",
  transducer: "headphones" as const,
  version: 2,
};

describe("AudiologyDashboard", () => {
  afterEach(() => {
    cleanup();
  });

  it("shows alerts and bilateral cards with ltr charts", () => {
    const view = render(
      <NextIntlClientProvider
        locale="en"
        messages={{ audiology: audiologyMessages }}
      >
        <AudiologyDashboard
          patientId="01ARZ3NDEKTSV4RRFFQ69G5FAV"
          audiogram={audiogram}
          history={[audiogram]}
          overlayCandidates={[]}
          overlayIds={new Set()}
          onToggleOverlay={() => undefined}
        />
      </NextIntlClientProvider>,
    );
    expect(view.getByTestId(testIds.audiology.dashboard)).toBeTruthy();
    expect(view.getByTestId(testIds.audiology.alertAsymmetry)).toBeTruthy();
    expect(
      view.getByTestId(testIds.audiology.chartRight).closest('[dir="ltr"]'),
    ).toBeTruthy();
    expect(
      view.getByTestId(testIds.audiology.evolutionChart).getAttribute("dir"),
    ).toBe("ltr");
  });
});
