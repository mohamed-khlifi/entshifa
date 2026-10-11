import { render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";

import { EarTracking } from "./EarTracking";
import type { PatientFlagRead } from "@/lib/api/generated";
import { patientEarFlagTestId, testIds } from "@/lib/test/test-id";
import formsMessages from "../../../../../../packages/i18n-messages/en/forms.json";
import patientsMessages from "../../../../../../packages/i18n-messages/en/patients.json";

function flag(
  flagCode: string,
  laterality: string | null,
  publicId: string,
): PatientFlagRead {
  return {
    publicId,
    flagCode,
    laterality,
    severity: null,
    detail: null,
    startedOn: "2026-06-02",
    endedOn: null,
    isAuto: true,
    recordedByPublicId: null,
    version: 1,
  };
}

describe("EarTracking", () => {
  it("shows a tube, a cavity, and a cholesteatoma with the ear", () => {
    const view = render(
      <NextIntlClientProvider
        locale="en"
        messages={{ patients: patientsMessages, forms: formsMessages }}
      >
        <EarTracking
          flags={[
            flag("ventilation_tube", "right", "01ARZ3NDEKTSV4RRFFQ69G5FAV"),
            flag("mastoid_cavity", "left", "01ARZ3NDEKTSV4RRFFQ69G5FB2"),
            flag("cholesteatoma", "right", "01ARZ3NDEKTSV4RRFFQ69G5FB3"),
          ]}
        />
      </NextIntlClientProvider>,
    );
    const root = view.getByTestId(testIds.patients.headerEars);
    expect(root.textContent).toContain("Ventilation tube");
    expect(root.textContent).toContain("Right");
    expect(
      view.getByTestId(patientEarFlagTestId("mastoid_cavity", "left"))
        .textContent,
    ).toContain("Left");
    expect(
      view.getByTestId(patientEarFlagTestId("cholesteatoma", "right"))
        .textContent,
    ).toContain("Cholesteatoma");
  });
});
