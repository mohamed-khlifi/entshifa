import { describe, expect, it } from "vitest";

import {
  documentKindForPlan,
  mriOverrideRequired,
  overrideReasonAccepted,
  suggestedClinicalQuestion,
} from "./visit-documents";

describe("visit document helpers", () => {
  it("blocks MRI when a non-MRI-safe implant is active", () => {
    expect(mriOverrideRequired("mri_neck", ["pacemaker"])).toBe(true);
    expect(mriOverrideRequired("mri_iac_gadolinium", ["pregnancy"])).toBe(
      false,
    );
    expect(mriOverrideRequired("ct_neck_contrast", ["cochlear_implant"])).toBe(
      false,
    );
  });

  it("accepts only a real override reason", () => {
    expect(overrideReasonAccepted("short")).toBe(false);
    expect(overrideReasonAccepted("Conditional device, radiology agreed")).toBe(
      true,
    );
  });

  it("maps plan items onto the document that should open", () => {
    expect(documentKindForPlan("imaging_requested")).toBe("imaging");
    expect(documentKindForPlan("test_requested")).toBe("laboratory");
    expect(documentKindForPlan("medication")).toBeNull();
  });

  it("joins recorded visit facts for the clinical question", () => {
    expect(
      suggestedClinicalQuestion({
        complaints: ["nasal obstruction"],
        diagnoses: ["deviated septum"],
        assessment: " plan surgery ",
      }),
    ).toBe("nasal obstruction · deviated septum · plan surgery");
  });
});
