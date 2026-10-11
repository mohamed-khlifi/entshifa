import { describe, expect, it, vi } from "vitest";

import {
  SUGGESTED_DAYS,
  addCalendarDays,
  draftIssues,
  emptyDraft,
  toWrite,
} from "./draft";

vi.mock("@/features/attachments", () => ({
  dateTimeLocalToUtcIso: (value: string) =>
    value.length > 0 ? `${value}:00.000Z` : null,
}));

describe("office procedure draft", () => {
  it("suggests the appendix C pack removal date and omits it for cautery", () => {
    const draft = emptyDraft("2026-06-02T09:15");
    expect(draft.packRemovalDate).toBe(
      addCalendarDays("2026-06-02", SUGGESTED_DAYS.packRemoval),
    );
    draft.systolic = "150";
    draft.diastolic = "90";
    const cautery = toWrite(draft, "01PATIENT", "en", "UTC");
    expect(cautery?.detail.subtype).toBe("epistaxis_management");
    if (cautery?.detail.subtype === "epistaxis_management") {
      expect(cautery.detail.packRemovalDate).toBeNull();
    }
    draft.epistaxisMethod = "anterior_pack";
    const packed = toWrite(draft, "01PATIENT", "en", "UTC");
    if (packed?.detail.subtype === "epistaxis_management") {
      expect(packed.detail.packRemovalDate).toBe("2026-06-04");
      expect(packed.detail.packType).toBe("merocel");
    }
  });

  it("requires a side for epistaxis and a laboratory for biopsy", () => {
    const draft = emptyDraft("2026-06-02T09:15");
    draft.laterality = "bilateral";
    draft.systolic = "120";
    draft.diastolic = "80";
    expect(draftIssues(draft, "en")).toContain("laterality");
    draft.subtype = "oral_pharyngeal_biopsy";
    draft.laterality = "na";
    draft.laboratoryText = "";
    expect(draftIssues(draft, "fr")).toContain("laboratory");
  });

  it("does not schedule a recall field for peritonsillar drainage", () => {
    const draft = emptyDraft("2026-06-02T09:15");
    draft.subtype = "peritonsillar_drainage";
    draft.volumeMl = "4";
    const body = toWrite(draft, "01PATIENT", "en", "UTC");
    expect(body?.detail.subtype).toBe("peritonsillar_drainage");
  });
});
