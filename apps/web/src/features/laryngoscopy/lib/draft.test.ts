import { describe, expect, it } from "vitest";

import type { LaryngoscopyExamRead } from "@/lib/api/generated";

import {
  applyTemplate,
  compareStructures,
  draftIssue,
  emptyDraft,
  scoreTrend,
  templateFocus,
  toCreateBody,
  VOCAL_FOLD_CODE,
} from "./draft";

const performedAt = "2026-10-11T10:00";
const patientId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

function exam(
  publicId: string,
  at: string,
  rfsScore: number | null,
): LaryngoscopyExamRead {
  return {
    publicId,
    version: 1,
    procedureId: "01ARZ3NDEKTSV4RRFFQ69G5FB1",
    procedureStatus: "draft",
    patientId,
    encounterId: null,
    performedAt: at,
    laterality: "bilateral",
    anesthesia: "topical_spray",
    setting: "office",
    instrument: null,
    indicationText: null,
    tolerance: null,
    scopeType: "flexible_fiberoptic",
    vocalFoldRight: { mobility: "normal", position: null },
    vocalFoldLeft: { mobility: "normal", position: null },
    glotticClosure: "complete",
    supraglotticPattern: null,
    stroboscopyPerformed: false,
    symmetry: null,
    periodicity: null,
    amplitudeRight: null,
    amplitudeLeft: null,
    mucosalWaveRight: null,
    mucosalWaveLeft: null,
    phaseClosure: null,
    phaseSymmetry: null,
    verticalLevel: null,
    nonVibratingSegment: null,
    feesPerformed: false,
    rfsScore,
    refluxFindingScore: null,
    grbas: null,
    pasScore: null,
    consistencies: [],
    residueSites: [],
    structures: [],
    lesions: [],
    scores: [],
    conclusionText: null,
    createdAt: at,
    updatedAt: at,
  };
}

describe("laryngoscopy draft", () => {
  it("builds a pre-thyroidectomy payload without computing scores", () => {
    const draft = applyTemplate(emptyDraft(performedAt), "pre_thyroid");
    const written = toCreateBody(draft, patientId, "2026-10-11T08:00:00.000Z");
    expect(written.ok).toBe(true);
    if (!written.ok) {
      return;
    }
    expect(written.body.vocalFoldRight.mobility).toBe("normal");
    expect(written.body.vocalFoldLeft.mobility).toBe("normal");
    expect(written.body.glotticClosure).toBe("complete");
    expect(
      (written.body.structures ?? []).every(
        (row) =>
          row.bodySiteCode === VOCAL_FOLD_CODE ||
          row.bodySiteCode === "ANAT.LARYNX.ARYTENOID" ||
          row.status === "not_examined",
      ),
    ).toBe(true);
    expect(written.body.refluxFindingScore).toBeNull();
  });

  it("focuses paralysis folds and enables FEES without computing PAS", () => {
    const paralysis = applyTemplate(emptyDraft(performedAt), "paralysis");
    expect(templateFocus("paralysis")).toBe("larynx.vocal-fold");
    const fold = paralysis.structures.find(
      (row) =>
        row.bodySiteCode === VOCAL_FOLD_CODE && row.laterality === "right",
    );
    expect(fold?.status).toBe("unset");
    const fees = applyTemplate(emptyDraft(performedAt), "fees");
    expect(fees.includeFees).toBe(true);
    expect(draftIssue(fees, "2026-10-11T08:00:00.000Z")).toBe("fees");
  });

  it("blocks an immobile fold without a position", () => {
    const draft = emptyDraft(performedAt);
    draft.vocalFoldRight.mobility = "immobile";
    expect(draftIssue(draft, "2026-10-11T08:00:00.000Z")).toBe("position");
  });

  it("highlights a changed structure against the previous exam", () => {
    const current = applyTemplate(emptyDraft(performedAt), "pre_thyroid");
    const rows = compareStructures(current.structures, [
      {
        bodySite: {
          conceptId: "01ARZ3NDEKTSV4RRFFQ69G5FB5",
          code: VOCAL_FOLD_CODE,
          display: "Vocal fold",
        },
        laterality: "right",
        status: "abnormal",
        finding: {
          conceptId: "01ARZ3NDEKTSV4RRFFQ69G5FB4",
          code: "FIND.LARYNX.EDEMA",
          display: "Edema",
        },
      },
    ]);
    const fold = rows.find(
      (row) =>
        row.bodySiteCode === VOCAL_FOLD_CODE && row.laterality === "right",
    );
    expect(fold?.change).toBe("changed");
  });

  it("trends server totals only", () => {
    const points = scoreTrend([
      exam("01ARZ3NDEKTSV4RRFFQ69G5FB2", "2026-01-01T00:00:00.000Z", 2),
      exam("01ARZ3NDEKTSV4RRFFQ69G5FB3", "2026-02-01T00:00:00.000Z", 8),
    ]);
    expect(points[1]?.rfsScore).toBe(8);
    expect(points[1]?.rfsChanged).toBe(true);
  });
});
