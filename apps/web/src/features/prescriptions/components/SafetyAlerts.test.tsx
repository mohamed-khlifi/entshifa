import { render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";

import { SafetyAlerts } from "./SafetyAlerts";
import { testIds } from "@/lib/test/test-id";

const messages = {
  prescriptions: {
    safety: {
      title: "Safety checks",
      allergyConflict: "Allergy block",
      doseAboveMaximum: "Dose block",
      pediatricWeightMissing: "Weight required",
      ototoxic: "Ototoxic",
      duplicateClass: "Duplicate",
      pregnancy: "Pregnancy",
      breastfeeding: "Breastfeeding",
      unstructured: "Free text",
      unknown: "Review",
    },
    builder: {
      blocked: "Resolve the safety blocks before issuing.",
    },
  },
};

describe("SafetyAlerts", () => {
  it("shows a block before the prescription is issued", () => {
    const view = render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <SafetyAlerts
          blocked
          alerts={[
            {
              code: "prescription.pediatric_weight_missing",
              severity: "block",
              itemIndex: null,
              itemKey: null,
            },
          ]}
        />
      </NextIntlClientProvider>,
    );
    expect(
      view.getByTestId(testIds.prescriptions.blocked).textContent,
    ).toContain("Resolve the safety blocks");
    expect(
      view.getByTestId("prescriptions.alert.pediatric-weight-missing")
        .textContent,
    ).toContain("Weight required");
  });
});
