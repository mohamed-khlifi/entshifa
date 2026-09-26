import { render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";

import { PatientSafetyAlertBanner } from "../components/PatientSafetyAlertBanner";
import type { PatientFlagRead } from "@/lib/api/generated";

const messages = {
  patients: {
    alerts: {
      onlyHearingEar: "Only hearing ear",
    },
  },
};

function flag(flagCode: string): PatientFlagRead {
  return {
    publicId: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    flagCode,
    laterality: null,
    severity: null,
    detail: null,
    startedOn: "2020-01-01",
    endedOn: null,
    isAuto: false,
    recordedByPublicId: null,
    version: 1,
  };
}

describe("PatientSafetyAlertBanner", () => {
  it("renders the only hearing ear alert as an assertive banner", () => {
    const view = render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <PatientSafetyAlertBanner flags={[flag("only_hearing_ear")]} />
      </NextIntlClientProvider>,
    );
    const banner = view.getByTestId("patients.alert-only-hearing-ear");
    expect(banner.getAttribute("role")).toBe("alert");
    expect(banner.className).toContain("bg-destructive");
    expect(banner.textContent).toContain("Only hearing ear");
  });
});
