import { describe, expect, it, vi } from "vitest";

import { draftIssues, emptyDraft, toWrite } from "./draft";

vi.mock("@/features/attachments", () => ({
  dateTimeLocalToUtcIso: (value: string) =>
    value.length > 0 ? `${value}:00.000Z` : null,
}));

describe("otology draft", () => {
  it("requires a fork frequency when Weber is recorded", () => {
    const draft = emptyDraft("2026-06-02T09:15");
    draft.weber = "midline";
    expect(draftIssues(draft)).toContain("fork");
    expect(
      toWrite(draft, "01ARZ3NDEKTSV4RRFFQ69G5FAV", "UTC", "en"),
    ).toBeNull();
  });

  it("builds a right-ear tube insertion", () => {
    const draft = emptyDraft("2026-06-02T09:15");
    draft.laterality = "right";
    draft.subtype = "tube_insertion";
    draft.tubeModel = "shepard";
    draft.effusion = "serous";
    const body = toWrite(draft, "01ARZ3NDEKTSV4RRFFQ69G5FAV", "UTC", "en");
    expect(body?.create.procedure).toEqual({
      subtype: "tube_insertion",
      tubeModel: "shepard",
      effusion: "serous",
      complication: null,
    });
    expect(body?.create.laterality).toBe("right");
  });

  it("rejects a bilateral wick", () => {
    const draft = emptyDraft("2026-06-02T09:15");
    draft.subtype = "wick";
    expect(draftIssues(draft)).toContain("side");
  });
});
