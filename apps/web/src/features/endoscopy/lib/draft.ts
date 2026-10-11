import { nasalEndoscopyMap } from "@/lib/anatomy";
import {
  effectiveLaterality,
  regionStorageKey,
} from "@/lib/anatomy/examination-state";
import type {
  MapRegionDefinition,
  MapSide,
  RegionMark,
} from "@/lib/anatomy/types";
import type {
  EndoscopyCreate,
  EndoscopyExamRead,
  EndoscopyStructureRead,
  EndoscopyStructureWrite,
  EndoscopyUpdate,
} from "@/lib/api/generated";

/** Finding codes from the endoscopy catalog. Displays come from the value set. */
export const FINDING_NORMAL = "FIND.ENDO.NORMAL";
export const FINDING_NOT_VISUALIZED = "FIND.ENDO.NOT_VISUALIZED";
export const FINDING_UNKNOWN = "FIND.ENDO.UNKNOWN";

export const ABNORMAL_FINDINGS = [
  "FIND.ENDO.POLYP",
  "FIND.ENDO.EDEMA",
  "FIND.ENDO.DISCHARGE",
  "FIND.ENDO.CRUST",
  "FIND.ENDO.SYNECHIA",
] as const;

export const LK_ITEMS = [
  "polyps",
  "edema",
  "discharge",
  "scarring",
  "crusting",
] as const;

/** Each Lund-Kennedy item is an entered integer 0–2. The server sums them. */
export const LK_ITEM_CHOICES = [0, 1, 2] as const;

/**
 * Input bounds from engines.endoscopy.polyp_grade.SCALE_MAX.
 * The browser does not grade polyps.
 */
export const POLYP_GRADE_MAX = { meltzer: 4, lildholdt: 3 } as const;

/** Input bound from engines.endoscopy.adenoid. The browser does not score it. */
export const ADENOID_MAX = 100;

export const SCOPE_TYPES = [
  "flexible",
  "rigid_0",
  "rigid_30",
  "rigid_70",
] as const;

export const ANESTHESIA_TYPES = [
  "none",
  "topical_spray",
  "local_infiltration",
  "general",
] as const;

export const SETTINGS = ["office", "ot"] as const;

export const PROCEDURE_LATERALITIES = [
  "bilateral",
  "right",
  "left",
  "midline",
  "na",
] as const;

export const TOLERANCE_VALUES = [
  "well_tolerated",
  "mild_discomfort",
  "moderate_discomfort",
  "poorly_tolerated",
  "aborted",
] as const;

export const STRUCTURE_STATUSES = [
  "unset",
  "normal",
  "abnormal",
  "not_examined",
  "unknown",
] as const;

export type EndoscopyTemplate = "normal" | "post_fess" | "epistaxis";
export type StructureStatus = (typeof STRUCTURE_STATUSES)[number];
export type StructureLaterality = "right" | "left" | "midline";
export type LkItem = (typeof LK_ITEMS)[number];
export type PolypScaleName = keyof typeof POLYP_GRADE_MAX;
export type DraftIssue = "lk" | "polyp" | "adenoid" | "finding" | "performedAt";

export type LkSideDraft = Record<LkItem, number | null>;

export type StructureDraft = {
  bodySiteCode: string;
  laterality: StructureLaterality;
  status: StructureStatus;
  findingCode: string | null;
};

export type EndoscopyDraft = {
  performedAt: string;
  laterality: (typeof PROCEDURE_LATERALITIES)[number];
  anesthesia: (typeof ANESTHESIA_TYPES)[number];
  setting: (typeof SETTINGS)[number];
  scopeType: (typeof SCOPE_TYPES)[number];
  decongestantUsed: boolean;
  instrument: string;
  indicationText: string;
  tolerance: "" | (typeof TOLERANCE_VALUES)[number];
  conclusionText: string;
  lundKennedyRight: LkSideDraft;
  lundKennedyLeft: LkSideDraft;
  polypGradeRight: number | null;
  polypGradeLeft: number | null;
  adenoidObstructionPct: number | null;
  structures: StructureDraft[];
};

export type ComparisonChange = "changed" | "unchanged" | "not_recorded";

export type ComparisonRow = {
  bodySiteCode: string;
  laterality: StructureLaterality;
  previousStatus: string | null;
  previousDisplay: string | null;
  currentStatus: string | null;
  currentFindingCode: string | null;
  change: ComparisonChange;
};

export type ScoreTrendPoint = {
  examId: string;
  performedAt: string;
  lundKennedyTotal: number;
  modifiedLkTotal: number;
  polypGradeRight: number | null;
  polypGradeLeft: number | null;
  polypScale: string;
  adenoidObstructionPct: number | null;
  lundKennedyChanged: boolean;
};

type WriteBody = Omit<EndoscopyCreate, "patientPublicId">;

const POST_FESS = "ANAT.NASAL.POST_FESS";
const EPISTAXIS_SITES = new Set(["ANAT.NASAL.VESTIBULE", "ANAT.NASAL.SEPTUM"]);

function blankSide(): LkSideDraft {
  return {
    polyps: null,
    edema: null,
    discharge: null,
    scarring: null,
    crusting: null,
  };
}

function zeroSide(): LkSideDraft {
  return {
    polyps: 0,
    edema: 0,
    discharge: 0,
    scarring: 0,
    crusting: 0,
  };
}

function blankStructure(
  bodySiteCode: string,
  laterality: StructureLaterality,
  status: StructureStatus = "unset",
): StructureDraft {
  return {
    bodySiteCode,
    laterality,
    status,
    findingCode: findingForStatus(status, null),
  };
}

export function structureSlots(
  status: StructureStatus = "unset",
): StructureDraft[] {
  const rows: StructureDraft[] = [];
  for (const region of nasalEndoscopyMap.regions) {
    if (region.fixedLaterality === "midline") {
      rows.push(blankStructure(region.bodySiteCode, "midline", status));
      continue;
    }
    rows.push(blankStructure(region.bodySiteCode, "right", status));
    rows.push(blankStructure(region.bodySiteCode, "left", status));
  }
  return rows;
}

export function emptyDraft(performedAt: string): EndoscopyDraft {
  return {
    performedAt,
    laterality: "bilateral",
    anesthesia: "topical_spray",
    setting: "office",
    scopeType: "flexible",
    decongestantUsed: false,
    instrument: "",
    indicationText: "",
    tolerance: "",
    conclusionText: "",
    lundKennedyRight: blankSide(),
    lundKennedyLeft: blankSide(),
    polypGradeRight: null,
    polypGradeLeft: null,
    adenoidObstructionPct: null,
    structures: structureSlots(),
  };
}

function findingForStatus(
  status: StructureStatus,
  findingCode: string | null,
): string | null {
  if (status === "unset") {
    return null;
  }
  if (status === "normal") {
    return FINDING_NORMAL;
  }
  if (status === "not_examined") {
    return FINDING_NOT_VISUALIZED;
  }
  if (status === "unknown") {
    return FINDING_UNKNOWN;
  }
  if (
    findingCode !== null &&
    (ABNORMAL_FINDINGS as readonly string[]).includes(findingCode)
  ) {
    return findingCode;
  }
  return null;
}

export function isAbnormalFinding(code: string): boolean {
  return (ABNORMAL_FINDINGS as readonly string[]).includes(code);
}

export function polypGradeChoices(scale: PolypScaleName): number[] {
  const max = POLYP_GRADE_MAX[scale];
  return Array.from({ length: max + 1 }, (_, index) => index);
}

export function isPolypScale(value: string): value is PolypScaleName {
  return value === "meltzer" || value === "lildholdt";
}

export function applyTemplate(
  draft: EndoscopyDraft,
  template: EndoscopyTemplate,
): EndoscopyDraft {
  if (template === "normal") {
    return {
      ...draft,
      tolerance: draft.tolerance || "well_tolerated",
      lundKennedyRight: zeroSide(),
      lundKennedyLeft: zeroSide(),
      polypGradeRight: 0,
      polypGradeLeft: 0,
      structures: structureSlots("normal"),
    };
  }
  if (template === "post_fess") {
    return {
      ...draft,
      structures: structureSlots("not_examined").map((row) =>
        row.bodySiteCode === POST_FESS
          ? blankStructure(row.bodySiteCode, row.laterality, "unset")
          : row,
      ),
    };
  }
  return {
    ...draft,
    structures: structureSlots("not_examined").map((row) =>
      EPISTAXIS_SITES.has(row.bodySiteCode)
        ? blankStructure(row.bodySiteCode, row.laterality, "unset")
        : row,
    ),
  };
}

export function templateFocus(template: EndoscopyTemplate): string | null {
  if (template === "post_fess") {
    return "endo.post-fess";
  }
  if (template === "epistaxis") {
    return "endo.vestibule";
  }
  return null;
}

function sideFromExam(
  side: EndoscopyExamRead["lundKennedyRight"],
): LkSideDraft {
  return {
    polyps: side.polyps,
    edema: side.edema,
    discharge: side.discharge,
    scarring: side.scarring,
    crusting: side.crusting,
  };
}

function statusFromRead(status: string): StructureStatus {
  if (
    status === "normal" ||
    status === "abnormal" ||
    status === "not_examined" ||
    status === "unknown"
  ) {
    return status;
  }
  return "unset";
}

function lateralityFromRead(value: string): StructureLaterality | null {
  if (value === "right" || value === "left" || value === "midline") {
    return value;
  }
  return null;
}

export function draftFromExam(
  exam: EndoscopyExamRead,
  performedAt: string,
): EndoscopyDraft {
  const base = emptyDraft(performedAt);
  const slots = base.structures.map((slot) => {
    const match = exam.structures.find(
      (row) =>
        row.bodySite.code === slot.bodySiteCode &&
        row.laterality === slot.laterality,
    );
    if (!match) {
      return slot;
    }
    const laterality = lateralityFromRead(match.laterality);
    if (!laterality) {
      return slot;
    }
    const status = statusFromRead(match.status);
    return {
      bodySiteCode: slot.bodySiteCode,
      laterality,
      status,
      findingCode: match.finding.code ?? findingForStatus(status, null),
    };
  });
  const laterality = PROCEDURE_LATERALITIES.find(
    (value) => value === exam.laterality,
  );
  const anesthesia = ANESTHESIA_TYPES.find(
    (value) => value === exam.anesthesia,
  );
  const setting = SETTINGS.find((value) => value === exam.setting);
  const scopeType = SCOPE_TYPES.find((value) => value === exam.scopeType);
  const tolerance = TOLERANCE_VALUES.find((value) => value === exam.tolerance);
  return {
    ...base,
    performedAt,
    laterality: laterality ?? "bilateral",
    anesthesia: anesthesia ?? "topical_spray",
    setting: setting ?? "office",
    scopeType: scopeType ?? "flexible",
    decongestantUsed: exam.decongestantUsed,
    instrument: exam.instrument ?? "",
    indicationText: exam.indicationText ?? "",
    tolerance: tolerance ?? "",
    conclusionText: exam.conclusionText ?? "",
    lundKennedyRight: sideFromExam(exam.lundKennedyRight),
    lundKennedyLeft: sideFromExam(exam.lundKennedyLeft),
    polypGradeRight: exam.polypGradeRight,
    polypGradeLeft: exam.polypGradeLeft,
    adenoidObstructionPct: exam.adenoidObstructionPct,
    structures: slots,
  };
}

export function withStructureStatus(
  draft: EndoscopyDraft,
  bodySiteCode: string,
  laterality: StructureLaterality,
  status: StructureStatus,
): EndoscopyDraft {
  return {
    ...draft,
    structures: draft.structures.map((row) => {
      if (row.bodySiteCode !== bodySiteCode || row.laterality !== laterality) {
        return row;
      }
      return {
        ...row,
        status,
        findingCode: findingForStatus(status, row.findingCode),
      };
    }),
  };
}

export function withStructureFinding(
  draft: EndoscopyDraft,
  bodySiteCode: string,
  laterality: StructureLaterality,
  findingCode: string,
): EndoscopyDraft {
  const status = statusForFinding(findingCode);
  return {
    ...draft,
    structures: draft.structures.map((row) => {
      if (row.bodySiteCode !== bodySiteCode || row.laterality !== laterality) {
        return row;
      }
      return { ...row, status, findingCode };
    }),
  };
}

export function statusForFinding(findingCode: string): StructureStatus {
  if (findingCode === FINDING_NORMAL) {
    return "normal";
  }
  if (findingCode === FINDING_NOT_VISUALIZED) {
    return "not_examined";
  }
  if (findingCode === FINDING_UNKNOWN) {
    return "unknown";
  }
  return "abnormal";
}

export function withLkItem(
  draft: EndoscopyDraft,
  side: "right" | "left",
  item: LkItem,
  value: number,
): EndoscopyDraft {
  const key = side === "right" ? "lundKennedyRight" : "lundKennedyLeft";
  return {
    ...draft,
    [key]: { ...draft[key], [item]: value },
  };
}

function regionForCode(bodySiteCode: string): MapRegionDefinition | undefined {
  return nasalEndoscopyMap.regions.find(
    (region) => region.bodySiteCode === bodySiteCode,
  );
}

export function marksForSide(
  draft: EndoscopyDraft,
  side: MapSide,
): Record<string, RegionMark> {
  const marks: Record<string, RegionMark> = {};
  for (const region of nasalEndoscopyMap.regions) {
    const laterality = effectiveLaterality(region, side);
    if (
      laterality !== "right" &&
      laterality !== "left" &&
      laterality !== "midline"
    ) {
      continue;
    }
    const row = draft.structures.find(
      (item) =>
        item.bodySiteCode === region.bodySiteCode &&
        item.laterality === laterality,
    );
    if (!row || row.status === "unset") {
      continue;
    }
    const status = row.status === "unknown" ? "abnormal" : row.status;
    marks[regionStorageKey(laterality, region.id)] = {
      status,
      conceptCode: row.findingCode,
      dirty: true,
      confirmed: true,
    };
  }
  return marks;
}

export function applyMapFinding(
  draft: EndoscopyDraft,
  region: MapRegionDefinition,
  side: MapSide,
  findingCode: string,
): EndoscopyDraft {
  const laterality = effectiveLaterality(region, side);
  if (
    laterality !== "right" &&
    laterality !== "left" &&
    laterality !== "midline"
  ) {
    return draft;
  }
  return withStructureFinding(
    draft,
    region.bodySiteCode,
    laterality,
    findingCode,
  );
}

export function applyMapNormal(
  draft: EndoscopyDraft,
  region: MapRegionDefinition,
  side: MapSide,
): EndoscopyDraft {
  return applyMapFinding(draft, region, side, region.defaultNormalCode);
}

export function applyMapNotExamined(
  draft: EndoscopyDraft,
  region: MapRegionDefinition,
  side: MapSide,
): EndoscopyDraft {
  return applyMapFinding(draft, region, side, FINDING_NOT_VISUALIZED);
}

function lkReady(side: LkSideDraft): boolean {
  return LK_ITEMS.every((item) => {
    const value = side[item];
    return (
      value !== null && (LK_ITEM_CHOICES as readonly number[]).includes(value)
    );
  });
}

function lkPayload(side: LkSideDraft): Record<LkItem, number> | null {
  if (!lkReady(side)) {
    return null;
  }
  return {
    polyps: side.polyps ?? 0,
    edema: side.edema ?? 0,
    discharge: side.discharge ?? 0,
    scarring: side.scarring ?? 0,
    crusting: side.crusting ?? 0,
  };
}

export function draftIssue(
  draft: EndoscopyDraft,
  scale: PolypScaleName,
  performedAtIso: string | null,
): DraftIssue | null {
  if (!performedAtIso) {
    return "performedAt";
  }
  if (!lkReady(draft.lundKennedyRight) || !lkReady(draft.lundKennedyLeft)) {
    return "lk";
  }
  const right = draft.polypGradeRight;
  const left = draft.polypGradeLeft;
  const max = POLYP_GRADE_MAX[scale];
  if ((right === null) !== (left === null)) {
    return "polyp";
  }
  if (
    (right !== null && (right < 0 || right > max)) ||
    (left !== null && (left < 0 || left > max))
  ) {
    return "polyp";
  }
  const adenoid = draft.adenoidObstructionPct;
  if (adenoid !== null && (adenoid < 0 || adenoid > ADENOID_MAX)) {
    return "adenoid";
  }
  for (const row of draft.structures) {
    if (row.status === "unset") {
      continue;
    }
    if (row.findingCode !== findingForStatus(row.status, row.findingCode)) {
      return "finding";
    }
    if (row.status === "abnormal" && row.findingCode === null) {
      return "finding";
    }
  }
  return null;
}

function recordedStructures(draft: EndoscopyDraft): EndoscopyStructureWrite[] {
  const rows: EndoscopyStructureWrite[] = [];
  for (const row of draft.structures) {
    if (row.status === "unset" || row.findingCode === null) {
      continue;
    }
    if (row.status === "abnormal" && !isAbnormalFinding(row.findingCode)) {
      continue;
    }
    rows.push({
      bodySiteCode: row.bodySiteCode,
      laterality: row.laterality,
      status: row.status,
      findingCode: row.findingCode,
    });
  }
  return rows;
}

export function toWriteBody(
  draft: EndoscopyDraft,
  scale: PolypScaleName,
  performedAtIso: string | null,
): { ok: true; body: WriteBody } | { ok: false; issue: DraftIssue } {
  const issue = draftIssue(draft, scale, performedAtIso);
  if (issue || !performedAtIso) {
    return { ok: false, issue: issue ?? "performedAt" };
  }
  const right = lkPayload(draft.lundKennedyRight);
  const left = lkPayload(draft.lundKennedyLeft);
  if (!right || !left) {
    return { ok: false, issue: "lk" };
  }
  const structures = recordedStructures(draft);
  return {
    ok: true,
    body: {
      performedAt: performedAtIso,
      laterality: draft.laterality,
      anesthesia: draft.anesthesia,
      setting: draft.setting,
      scopeType: draft.scopeType,
      decongestantUsed: draft.decongestantUsed,
      instrument: draft.instrument.trim() || null,
      indicationText: draft.indicationText.trim() || null,
      tolerance: draft.tolerance || null,
      conclusionText: draft.conclusionText.trim() || null,
      lundKennedyRight: right,
      lundKennedyLeft: left,
      polypGradeRight: draft.polypGradeRight,
      polypGradeLeft: draft.polypGradeLeft,
      adenoidObstructionPct: draft.adenoidObstructionPct,
      structures,
    },
  };
}

export function toCreateBody(
  draft: EndoscopyDraft,
  patientId: string,
  scale: PolypScaleName,
  performedAtIso: string | null,
): { ok: true; body: EndoscopyCreate } | { ok: false; issue: DraftIssue } {
  const written = toWriteBody(draft, scale, performedAtIso);
  if (!written.ok) {
    return written;
  }
  return { ok: true, body: { ...written.body, patientPublicId: patientId } };
}

export function toUpdateBody(
  draft: EndoscopyDraft,
  version: number,
  scale: PolypScaleName,
  performedAtIso: string | null,
): { ok: true; body: EndoscopyUpdate } | { ok: false; issue: DraftIssue } {
  const written = toWriteBody(draft, scale, performedAtIso);
  if (!written.ok) {
    return written;
  }
  return { ok: true, body: { ...written.body, version } };
}

function structureDisplay(row: EndoscopyStructureRead): string | null {
  return row.finding.display ?? row.finding.code ?? null;
}

export function compareStructures(
  current: readonly StructureDraft[],
  previous: readonly EndoscopyStructureRead[],
): ComparisonRow[] {
  return structureSlots().map((slot) => {
    const currentRow = current.find(
      (row) =>
        row.bodySiteCode === slot.bodySiteCode &&
        row.laterality === slot.laterality,
    );
    const previousRow = previous.find(
      (row) =>
        row.bodySite.code === slot.bodySiteCode &&
        row.laterality === slot.laterality,
    );
    const currentRecorded =
      currentRow !== undefined && currentRow.status !== "unset";
    const currentStatus = currentRecorded ? currentRow.status : null;
    const currentFindingCode = currentRecorded ? currentRow.findingCode : null;
    const previousStatus = previousRow ? previousRow.status : null;
    const previousDisplay = previousRow ? structureDisplay(previousRow) : null;
    let change: ComparisonChange = "unchanged";
    if (!currentRecorded && !previousRow) {
      change = "not_recorded";
    } else if (!currentRecorded || !previousRow) {
      change = "changed";
    } else if (
      previousRow.status !== currentRow.status ||
      previousRow.finding.code !== currentRow.findingCode
    ) {
      change = "changed";
    }
    return {
      bodySiteCode: slot.bodySiteCode,
      laterality: slot.laterality,
      previousStatus,
      previousDisplay,
      currentStatus,
      currentFindingCode,
      change,
    };
  });
}

function occurredAt(value: string): number {
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

export function selectPreviousExam<
  T extends { publicId: string; performedAt: string },
>(
  exams: readonly T[],
  currentId: string | null,
  currentPerformedAt: string | null,
): T | null {
  const candidates = exams.filter((exam) => exam.publicId !== currentId);
  if (candidates.length === 0) {
    return null;
  }
  if (!currentPerformedAt) {
    return (
      [...candidates].sort(
        (left, right) =>
          occurredAt(right.performedAt) - occurredAt(left.performedAt),
      )[0] ?? null
    );
  }
  const currentTime = occurredAt(currentPerformedAt);
  const older = candidates.filter(
    (exam) => occurredAt(exam.performedAt) < currentTime,
  );
  const pool = older.length > 0 ? older : [];
  if (pool.length === 0) {
    return null;
  }
  return (
    [...pool].sort(
      (left, right) =>
        occurredAt(right.performedAt) - occurredAt(left.performedAt),
    )[0] ?? null
  );
}

export function scoreTrend(
  exams: readonly EndoscopyExamRead[],
): ScoreTrendPoint[] {
  const ordered = [...exams].sort(
    (left, right) =>
      occurredAt(left.performedAt) - occurredAt(right.performedAt),
  );
  return ordered.map((exam, index) => {
    const prior = index > 0 ? ordered[index - 1] : null;
    return {
      examId: exam.publicId,
      performedAt: exam.performedAt,
      lundKennedyTotal: exam.lundKennedyTotal,
      modifiedLkTotal: exam.modifiedLkTotal,
      polypGradeRight: exam.polypGradeRight,
      polypGradeLeft: exam.polypGradeLeft,
      polypScale: exam.polypScale,
      adenoidObstructionPct: exam.adenoidObstructionPct,
      lundKennedyChanged:
        prior !== null && prior.lundKennedyTotal !== exam.lundKennedyTotal,
    };
  });
}

export function regionById(regionId: string): MapRegionDefinition | null {
  return (
    nasalEndoscopyMap.regions.find((region) => region.id === regionId) ?? null
  );
}

export function regionBySite(bodySiteCode: string): MapRegionDefinition | null {
  return regionForCode(bodySiteCode) ?? null;
}
