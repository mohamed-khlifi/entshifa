import { dateTimeLocalToUtcIso } from "@/features/attachments";
import type {
  EarDeviceRead,
  OtologyCreate,
  OtologyExamRead,
  OtologyStructureWrite,
  OtologyUpdate,
} from "@/lib/api/generated";
import {
  markFinding,
  markNormal,
  markNotExamined,
  regionStorageKey,
} from "@/lib/anatomy/examination-state";
import type {
  MapRegionDefinition,
  MapSide,
  RegionMark,
} from "@/lib/anatomy/types";
import { tympanicMembraneMap } from "@/lib/anatomy/tympanic-membrane.map";

const CANAL = "ANAT.EAR.CANAL";
const SIDED = new Set([
  "wick",
  "tube_insertion",
  "tube_removal",
  "intratympanic_injection",
  "cavity_cleaning",
]);

export const METHODS = ["otoscopy", "microscopy"] as const;
export const LATERALITIES = ["right", "left", "bilateral"] as const;
export const WEBER = [
  "midline",
  "lateralizes_right",
  "lateralizes_left",
] as const;
export const RINNE = ["positive", "negative"] as const;
export const FORKS = ["256", "512"] as const;
export const MOBILITY = ["normal", "reduced", "absent", "hypermobile"] as const;
export const SUBTYPES = [
  "none",
  "wax_removal",
  "foreign_body",
  "wick",
  "tube_insertion",
  "tube_removal",
  "intratympanic_injection",
  "cavity_cleaning",
] as const;
export const DEVICE_STATUSES = [
  "in_place",
  "blocked",
  "extruded",
  "removed",
  "retained",
] as const;

export type OtologySubtype = (typeof SUBTYPES)[number];
export type DraftIssue =
  "fork" | "side" | "object" | "dose" | "device" | "performedAt";

export type OtologyDraft = {
  performedAt: string;
  method: (typeof METHODS)[number];
  laterality: (typeof LATERALITIES)[number];
  weber: (typeof WEBER)[number] | "";
  rinneRight: (typeof RINNE)[number] | "";
  rinneLeft: (typeof RINNE)[number] | "";
  fork: (typeof FORKS)[number] | "";
  mobilityRight: (typeof MOBILITY)[number] | "";
  mobilityLeft: (typeof MOBILITY)[number] | "";
  marks: Record<string, RegionMark>;
  subtype: OtologySubtype;
  waxMethod: "microsuction" | "curette" | "irrigation";
  completeness: "complete" | "partial";
  canalCondition: "clear" | "residual_wax" | "inflamed" | "traumatized";
  objectText: string;
  foreignBodyMethod: "microsuction" | "forceps" | "irrigation" | "hook";
  trauma: "none" | "canal" | "tympanic";
  wickType: "pope" | "ribbon" | "merocel";
  tubeModel: "shepard" | "armstrong" | "t_tube" | "bobbin" | "paparella";
  effusion: "none" | "serous" | "mucoid" | "purulent" | "bloody";
  complication: "" | "bleeding" | "otorrhea" | "vertigo" | "perforation";
  devicePublicId: string;
  drugCode:
    | "DRUG.IT.DEXAMETHASONE"
    | "DRUG.IT.METHYLPREDNISOLONE"
    | "DRUG.IT.GENTAMICIN";
  doseAmount: string;
  doseUnit: "mg" | "mL";
  indicationText: string;
  cavityCondition:
    "dry" | "moist" | "granulation" | "debris" | "exposed_structures";
  conclusionText: string;
  version: number | null;
  procedureId: string | null;
  procedureStatus: string;
  removalDueDate: string | null;
};

export function emptyDraft(performedAt: string): OtologyDraft {
  return {
    performedAt,
    method: "microscopy",
    laterality: "bilateral",
    weber: "",
    rinneRight: "",
    rinneLeft: "",
    fork: "",
    mobilityRight: "",
    mobilityLeft: "",
    marks: {},
    subtype: "none",
    waxMethod: "microsuction",
    completeness: "complete",
    canalCondition: "clear",
    objectText: "",
    foreignBodyMethod: "microsuction",
    trauma: "none",
    wickType: "pope",
    tubeModel: "shepard",
    effusion: "none",
    complication: "",
    devicePublicId: "",
    drugCode: "DRUG.IT.DEXAMETHASONE",
    doseAmount: "",
    doseUnit: "mg",
    indicationText: "",
    cavityCondition: "dry",
    conclusionText: "",
    version: null,
    procedureId: null,
    procedureStatus: "draft",
    removalDueDate: null,
  };
}

export function draftFromExam(
  exam: OtologyExamRead,
  performedAt: string,
): OtologyDraft {
  const draft = emptyDraft(performedAt);
  draft.method = exam.method === "otoscopy" ? "otoscopy" : "microscopy";
  draft.laterality = isLaterality(exam.laterality)
    ? exam.laterality
    : "bilateral";
  draft.weber = isOneOf(exam.weber, WEBER) ? exam.weber : "";
  draft.rinneRight = isOneOf(exam.rinneRight, RINNE) ? exam.rinneRight : "";
  draft.rinneLeft = isOneOf(exam.rinneLeft, RINNE) ? exam.rinneLeft : "";
  draft.fork =
    exam.forkFrequencyHz === 256
      ? "256"
      : exam.forkFrequencyHz === 512
        ? "512"
        : "";
  draft.mobilityRight = isOneOf(exam.mobilityRight, MOBILITY)
    ? exam.mobilityRight
    : "";
  draft.mobilityLeft = isOneOf(exam.mobilityLeft, MOBILITY)
    ? exam.mobilityLeft
    : "";
  draft.conclusionText = exam.conclusionText ?? "";
  draft.version = exam.version;
  draft.procedureId = exam.procedureId;
  draft.procedureStatus = exam.procedureStatus;
  draft.marks = marksFromStructures(exam);
  applyOffice(draft, exam);
  return draft;
}

export function draftIssues(draft: OtologyDraft): DraftIssue[] {
  const issues: DraftIssue[] = [];
  if (!draft.performedAt) {
    issues.push("performedAt");
  }
  const tuning = [draft.weber, draft.rinneRight, draft.rinneLeft].some(Boolean);
  if (tuning && !draft.fork) {
    issues.push("fork");
  }
  if (SIDED.has(draft.subtype) && draft.laterality === "bilateral") {
    issues.push("side");
  }
  if (draft.subtype === "foreign_body" && !draft.objectText.trim()) {
    issues.push("object");
  }
  if (draft.subtype === "intratympanic_injection") {
    const dose = Number(draft.doseAmount);
    if (
      !draft.doseAmount.trim() ||
      Number.isNaN(dose) ||
      dose <= 0 ||
      dose > 100
    ) {
      issues.push("dose");
    }
  }
  if (draft.subtype === "tube_removal" && draft.devicePublicId.length !== 26) {
    issues.push("device");
  }
  return issues;
}

export function toWrite(
  draft: OtologyDraft,
  patientId: string,
  timeZone: string,
  locale: "en" | "fr" | "ar",
): { create: OtologyCreate; update: OtologyUpdate } | null {
  if (draftIssues(draft).length > 0) {
    return null;
  }
  const performedAt = dateTimeLocalToUtcIso(draft.performedAt, timeZone);
  if (!performedAt) {
    return null;
  }
  const shared = {
    performedAt,
    laterality: draft.laterality,
    anesthesia: "none" as const,
    setting: "office" as const,
    method: draft.method,
    weber: draft.weber || null,
    rinneRight: draft.rinneRight || null,
    rinneLeft: draft.rinneLeft || null,
    forkFrequencyHz: forkHz(draft.fork),
    mobilityRight: draft.mobilityRight || null,
    mobilityLeft: draft.mobilityLeft || null,
    structures: structuresFromMarks(draft.marks),
    procedure: procedureBlock(draft, locale),
    conclusionText: draft.conclusionText.trim() || null,
  };
  return {
    create: { ...shared, patientPublicId: patientId },
    update: { ...shared, version: draft.version ?? 1 },
  };
}

export function applyMapNormal(
  draft: OtologyDraft,
  region: MapRegionDefinition,
  side: MapSide,
): OtologyDraft {
  return withMark(draft, region, side, markNormal(region));
}

export function applyMapFinding(
  draft: OtologyDraft,
  region: MapRegionDefinition,
  side: MapSide,
  code: string,
): OtologyDraft {
  return withMark(draft, region, side, markFinding(code));
}

export function applyMapNotExamined(
  draft: OtologyDraft,
  region: MapRegionDefinition,
  side: MapSide,
): OtologyDraft {
  return withMark(draft, region, side, markNotExamined());
}

export function marksForSide(
  draft: OtologyDraft,
  side: MapSide,
): Record<string, RegionMark> {
  const marks: Record<string, RegionMark> = {};
  for (const region of tympanicMembraneMap.regions) {
    const mark = draft.marks[regionStorageKey(side, region.id)];
    if (mark) {
      marks[regionStorageKey(side, region.id)] = mark;
    }
  }
  return marks;
}

function withMark(
  draft: OtologyDraft,
  region: MapRegionDefinition,
  side: MapSide,
  mark: RegionMark,
): OtologyDraft {
  return {
    ...draft,
    marks: { ...draft.marks, [regionStorageKey(side, region.id)]: mark },
  };
}

function structuresFromMarks(
  marks: Record<string, RegionMark>,
): OtologyStructureWrite[] {
  const rows: OtologyStructureWrite[] = [];
  for (const region of tympanicMembraneMap.regions) {
    for (const side of ["right", "left"] as const) {
      const mark = marks[regionStorageKey(side, region.id)];
      if (!mark) {
        continue;
      }
      const findingCode = findingFor(region, mark);
      if (!findingCode) {
        continue;
      }
      rows.push({
        bodySiteCode: region.bodySiteCode,
        laterality: side,
        status: mark.status,
        findingCode,
        mapRegionCode: region.id,
      });
    }
  }
  return rows;
}

function findingFor(
  region: MapRegionDefinition,
  mark: RegionMark,
): string | null {
  if (mark.status === "normal") {
    return region.defaultNormalCode;
  }
  if (mark.status === "not_examined") {
    return region.bodySiteCode === CANAL
      ? "FIND.CANAL.NOT_VISUALIZED"
      : "FIND.TM.NOT_VISUALIZED";
  }
  return mark.conceptCode;
}

function forkHz(value: OtologyDraft["fork"]): 256 | 512 | null {
  if (value === "256") {
    return 256;
  }
  if (value === "512") {
    return 512;
  }
  return null;
}

function procedureBlock(
  draft: OtologyDraft,
  locale: "en" | "fr" | "ar",
): OtologyCreate["procedure"] {
  switch (draft.subtype) {
    case "none":
      return null;
    case "wax_removal":
      return {
        subtype: "wax_removal",
        method: draft.waxMethod,
        completeness: draft.completeness,
        canalCondition: draft.canalCondition,
      };
    case "foreign_body":
      return {
        subtype: "foreign_body",
        objectText: draft.objectText.trim(),
        objectLocale: locale,
        method: draft.foreignBodyMethod,
        trauma: draft.trauma,
      };
    case "wick":
      return { subtype: "wick", wickType: draft.wickType };
    case "tube_insertion":
      return {
        subtype: "tube_insertion",
        tubeModel: draft.tubeModel,
        effusion: draft.effusion,
        complication: draft.complication || null,
      };
    case "tube_removal":
      return { subtype: "tube_removal", devicePublicId: draft.devicePublicId };
    case "intratympanic_injection":
      return {
        subtype: "intratympanic_injection",
        drugCode: draft.drugCode,
        doseAmount: draft.doseAmount,
        doseUnit: draft.doseUnit,
        indicationText: draft.indicationText.trim() || null,
        indicationLocale: draft.indicationText.trim() ? locale : null,
      };
    case "cavity_cleaning":
      return { subtype: "cavity_cleaning", condition: draft.cavityCondition };
  }
}

function marksFromStructures(
  exam: OtologyExamRead,
): Record<string, RegionMark> {
  const marks: Record<string, RegionMark> = {};
  for (const row of exam.structures) {
    if (row.laterality !== "right" && row.laterality !== "left") {
      continue;
    }
    const region = tympanicMembraneMap.regions.find(
      (item) => item.id === row.mapRegionCode,
    );
    if (!region || !row.finding.code) {
      continue;
    }
    const mark =
      row.status === "not_examined"
        ? markNotExamined()
        : row.status === "normal"
          ? markNormal(region)
          : markFinding(row.finding.code);
    marks[regionStorageKey(row.laterality, region.id)] = mark;
  }
  return marks;
}

function applyOffice(draft: OtologyDraft, exam: OtologyExamRead): void {
  const office = exam.procedure;
  if (!office) {
    return;
  }
  const payload = office.payload as Record<string, string | null>;
  draft.removalDueDate = office.removalDueDate;
  if (!isSubtype(office.subtype) || office.subtype === "none") {
    return;
  }
  draft.subtype = office.subtype;
  draft.waxMethod = isOneOf(payload.method, [
    "microsuction",
    "curette",
    "irrigation",
  ] as const)
    ? payload.method
    : draft.waxMethod;
  draft.completeness =
    payload.completeness === "partial" ? "partial" : "complete";
  if (
    payload.canalCondition === "clear" ||
    payload.canalCondition === "residual_wax" ||
    payload.canalCondition === "inflamed" ||
    payload.canalCondition === "traumatized"
  ) {
    draft.canalCondition = payload.canalCondition;
  }
  draft.objectText = payload.objectText ?? "";
  if (
    payload.method === "forceps" ||
    payload.method === "hook" ||
    payload.method === "microsuction" ||
    payload.method === "irrigation"
  ) {
    draft.foreignBodyMethod = payload.method;
  }
  if (
    payload.trauma === "none" ||
    payload.trauma === "canal" ||
    payload.trauma === "tympanic"
  ) {
    draft.trauma = payload.trauma;
  }
  if (
    payload.wickType === "pope" ||
    payload.wickType === "ribbon" ||
    payload.wickType === "merocel"
  ) {
    draft.wickType = payload.wickType;
  }
  if (
    payload.tubeModel === "shepard" ||
    payload.tubeModel === "armstrong" ||
    payload.tubeModel === "t_tube" ||
    payload.tubeModel === "bobbin" ||
    payload.tubeModel === "paparella"
  ) {
    draft.tubeModel = payload.tubeModel;
  }
  if (
    payload.effusion === "none" ||
    payload.effusion === "serous" ||
    payload.effusion === "mucoid" ||
    payload.effusion === "purulent" ||
    payload.effusion === "bloody"
  ) {
    draft.effusion = payload.effusion;
  }
  if (
    payload.complication === "bleeding" ||
    payload.complication === "otorrhea" ||
    payload.complication === "vertigo" ||
    payload.complication === "perforation"
  ) {
    draft.complication = payload.complication;
  }
  draft.devicePublicId = payload.devicePublicId ?? "";
  if (
    payload.drugCode === "DRUG.IT.DEXAMETHASONE" ||
    payload.drugCode === "DRUG.IT.METHYLPREDNISOLONE" ||
    payload.drugCode === "DRUG.IT.GENTAMICIN"
  ) {
    draft.drugCode = payload.drugCode;
  }
  draft.doseAmount = payload.doseAmount ?? "";
  draft.doseUnit = payload.doseUnit === "mL" ? "mL" : "mg";
  draft.indicationText = payload.indicationText ?? "";
  if (
    payload.condition === "dry" ||
    payload.condition === "moist" ||
    payload.condition === "granulation" ||
    payload.condition === "debris" ||
    payload.condition === "exposed_structures"
  ) {
    draft.cavityCondition = payload.condition;
  }
}

export function openTubeDevices(
  devices: readonly EarDeviceRead[],
): EarDeviceRead[] {
  return devices.filter(
    (row) =>
      row.deviceType === "ventilation_tube" &&
      (row.status === "in_place" ||
        row.status === "blocked" ||
        row.status === "retained"),
  );
}

function isLaterality(value: string): value is OtologyDraft["laterality"] {
  return value === "right" || value === "left" || value === "bilateral";
}

function isSubtype(value: string): value is OtologySubtype {
  return (SUBTYPES as readonly string[]).includes(value);
}

function isOneOf<T extends string>(
  value: string | null | undefined,
  allowed: readonly T[],
): value is T {
  return value != null && (allowed as readonly string[]).includes(value);
}
