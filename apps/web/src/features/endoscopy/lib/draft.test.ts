import { describe, expect, it } from "vitest";

import type { EndoscopyExamRead } from "@/lib/api/generated";

import {
  applyTemplate,
  compareStructures,
  draftIssue,
  emptyDraft,
  scoreTrend,
  selectPreviousExam,
  structureSlots,
  toCreateBody,
} from "./draft";

const performedAt = "2026-10-11T10:00";

function side(total: number) {
  return {
    polyps: 0,
    edema: 0,
    discharge: 0,
    scarring: 0,
    crusting: 0,
    total,
  };
}

function exam(
  publicId: string,
  at: string,
  total: number,
  structures: EndoscopyExamRead["structures"] = [],
): EndoscopyExamRead {
  return {
    publicId,
    version: 1,
    procedureId: "01ARZ3NDEKTSV4RRFFQ69G5FB1",
    procedureStatus: "draft",
    patientId: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    encounterId: null,
    performedAt: at,
    laterality: "bilateral",
    anesthesia: "topical_spray",
    setting: "office",
    instrument: null,
    indicationText: null,
    tolerance: null,
    scopeType: "flexible",
    decongestantUsed: false,
    lundKennedyRight: side(0),
    lundKennedyLeft: side(0),
    lundKennedyTotal: total,
    modifiedLkRight: 0,
    modifiedLkLeft: 0,
    modifiedLkTotal: 0,
    polypGradeRight: 0,
    polypGradeLeft: 0,
    polypScale: "meltzer",
    adenoidObstructionPct: null,
    conclusionText: null,
    structures,
    scores: [],
    createdAt: at,
    updatedAt: at,
  };
}

describe("endoscopy draft", () => {
  it("documents a normal endoscopy without computing a total", () => {
    const draft = applyTemplate(emptyDraft(performedAt), "normal");
    const written = toCreateBody(
      draft,
      "01ARZ3NDEKTSV4RRFFQ69G5FAV",
      "meltzer",
      "2026-10-11T08:00:00.000Z",
    );
    expect(written.ok).toBe(true);
    if (!written.ok) {
      return;
    }
    expect(written.body.structures).toHaveLength(structureSlots().length);
    expect(
      written.body.structures?.every(
        (row) =>
          row.status === "normal" && row.findingCode === "FIND.ENDO.NORMAL",
      ),
    ).toBe(true);
    expect(written.body.lundKennedyRight).toEqual({
      polyps: 0,
      edema: 0,
      discharge: 0,
      scarring: 0,
      crusting: 0,
    });
    expect(written.body).not.toHaveProperty("lundKennedyTotal");
    expect(draftIssue(draft, "meltzer", "2026-10-11T08:00:00.000Z")).toBeNull();
  });

  it("leaves the post-FESS cavity for the doctor to record", () => {
    const draft = applyTemplate(emptyDraft(performedAt), "post_fess");
    const cavity = draft.structures.find(
      (row) => row.bodySiteCode === "ANAT.NASAL.POST_FESS",
    );
    expect(cavity?.status).toBe("unset");
    expect(
      draft.structures.some(
        (row) =>
          row.bodySiteCode !== "ANAT.NASAL.POST_FESS" &&
          row.status === "not_examined",
      ),
    ).toBe(true);
  });

  it("highlights a structure that differs from the previous exam", () => {
    const current = applyTemplate(emptyDraft(performedAt), "normal");
    const rows = compareStructures(current.structures, [
      {
        bodySite: {
          conceptId: "01ARZ3NDEKTSV4RRFFQ69G5FB3",
          code: "ANAT.NASAL.VESTIBULE",
          display: "Vestibule",
        },
        laterality: "right",
        status: "abnormal",
        finding: {
          conceptId: "01ARZ3NDEKTSV4RRFFQ69G5FB4",
          code: "FIND.ENDO.POLYP",
          display: "Polyp",
        },
      },
    ]);
    const vestibule = rows.find(
      (row) =>
        row.bodySiteCode === "ANAT.NASAL.VESTIBULE" &&
        row.laterality === "right",
    );
    expect(vestibule?.change).toBe("changed");
    expect(vestibule?.previousDisplay).toBe("Polyp");
  });

  it("orders the score trend from stored totals", () => {
    const older = exam(
      "01ARZ3NDEKTSV4RRFFQ69G5FB2",
      "2026-01-01T00:00:00.000Z",
      4,
    );
    const newer = exam(
      "01ARZ3NDEKTSV4RRFFQ69G5FB0",
      "2026-06-01T00:00:00.000Z",
      4,
    );
    expect(
      selectPreviousExam([newer, older], newer.publicId, newer.performedAt)
        ?.publicId,
    ).toBe(older.publicId);
    const trend = scoreTrend([newer, older]);
    expect(trend.map((point) => point.examId)).toEqual([
      older.publicId,
      newer.publicId,
    ]);
    expect(trend[1]?.lundKennedyChanged).toBe(false);
    expect(trend[0]?.lundKennedyTotal).toBe(4);
  });
});
