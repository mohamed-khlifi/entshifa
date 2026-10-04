import { describe, expect, it } from "vitest";

import type { EncounterRead } from "@/lib/api/generated";
import { selectCopySource } from "@/features/examination/lib/copy-source";

const patient = "01PATIENT00000000000000000";

describe("selectCopySource", () => {
  it("copies the previous visit when the open encounter is a draft", () => {
    const draft = encounter("01DRAFT0000000000000000000", "draft");
    const signed = encounter("01SIGNED000000000000000000", "signed");
    expect(selectCopySource([draft, signed], draft.publicId)?.publicId).toBe(
      signed.publicId,
    );
  });

  it("copies the visit the clinician is reading when it is already signed", () => {
    const signed = encounter("01SIGNED000000000000000000", "signed");
    const older = encounter("01OLDER0000000000000000000", "signed");
    expect(selectCopySource([signed, older], signed.publicId)?.publicId).toBe(
      signed.publicId,
    );
  });

  it("has nothing to copy from a single empty draft", () => {
    const draft = encounter("01DRAFT0000000000000000000", "draft");
    expect(selectCopySource([draft], draft.publicId)).toBeNull();
  });
});

function encounter(publicId: string, status: string): EncounterRead {
  return {
    addenda: [],
    clinicianPublicId: "01CLINICIAN000000000000000",
    complaints: [],
    encounterType: "consultation",
    patientPublicId: patient,
    publicId,
    signatures: [],
    sitePublicId: "01SITE000000000000000000000",
    startedAt: "2026-05-01T09:00:00.000Z",
    status,
    version: 1,
  };
}
