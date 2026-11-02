import { cleanup, render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { testIds } from "@/lib/test/test-id";
import audiologyMessages from "../../../../../../packages/i18n-messages/en/audiology.json";

import { TympanogramPanel } from "./TympanogramPanel";

vi.mock("../hooks/use-audiology", () => ({
  usePatientSpeechAudiometry: () => ({ data: { items: [] } }),
  usePatientTympanograms: () => ({ data: { items: [] } }),
  useSaveSpeechAudiometry: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useSaveTympanogram: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useInterpretTympanogram: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

vi.mock("@/providers/permission-provider", () => ({
  usePermission: () => false,
}));

describe("TympanogramPanel", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders speech and tympanometry summary sections", () => {
    const view = render(
      <NextIntlClientProvider
        locale="en"
        messages={{ audiology: audiologyMessages }}
      >
        <TympanogramPanel
          patientId="01ARZ3NDEKTSV4RRFFQ69G5FAV"
          audiogram={null}
        />
      </NextIntlClientProvider>,
    );
    expect(view.getByTestId(testIds.audiology.tympanogramPanel)).toBeTruthy();
  });
});
