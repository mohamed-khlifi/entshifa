import { cleanup, render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { testIds } from "@/lib/test/test-id";
import audiologyMessages from "../../../../../../packages/i18n-messages/en/audiology.json";

import { HearingDevicesPanel } from "./HearingDevicesPanel";

vi.mock("../hooks/use-audiology", () => ({
  usePatientHearingDevices: () => ({
    data: { items: [] },
    isLoading: false,
    isError: false,
  }),
  useCreateHearingDevice: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useEvaluateCandidacy: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
    data: undefined,
  }),
}));

vi.mock("@/providers/permission-provider", () => ({
  usePermission: () => true,
}));

describe("HearingDevicesPanel", () => {
  afterEach(() => cleanup());

  it("renders device panel root", () => {
    const { getByTestId } = render(
      <NextIntlClientProvider
        locale="en"
        messages={{ audiology: audiologyMessages }}
      >
        <HearingDevicesPanel
          patientId="01ARZ3NDEKTSV4RRFFQ69G5FAV"
          audiogramPublicId={null}
        />
      </NextIntlClientProvider>,
    );
    expect(getByTestId(testIds.audiology.hearingDevicesPanel)).toBeTruthy();
  });
});
