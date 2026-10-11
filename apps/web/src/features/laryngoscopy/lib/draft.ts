import { larynxMap } from "@/lib/anatomy";
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
  FeesWrite,
  GrbasWrite,
  LaryngoscopyCreate,
  LaryngoscopyExamRead,
  LaryngoscopyStructureRead,
  LaryngoscopyStructureWrite,
  LaryngoscopyUpdate,
  RefluxFindingScoreWrite,
  StroboscopyWrite,
  VocalFoldLesionRead,
  VocalFoldLesionWrite,
  VocalFoldWrite,
} from "@/lib/api/generated";

export const FINDING_NORMAL = "FIND.LARYNX.NORMAL";
export const FINDING_NOT_VISUALIZED = "FIND.LARYNX.NOT_VISUALIZED";
export const FINDING_UNKNOWN = "FIND.LARYNX.UNKNOWN";
export const REINKE_CODE = "FIND.LARYNX.REINKE_EDEMA";
export const VOCAL_FOLD_CODE = "ANAT.LARYNX.VOCAL_FOLD";

export const ABNORMAL_FINDINGS = [
  "FIND.LARYNX.EDEMA",
  "FIND.LARYNX.ERYTHEMA",
  "FIND.LARYNX.SECRETIONS",
  "FIND.LARYNX.POOLING",
  "FIND.LARYNX.PACHYDERMIA",
] as const;

export const LESION_FINDINGS = [
  "FIND.LARYNX.NODULE",
  "FIND.LARYNX.POLYP",
  "FIND.LARYNX.CYST",
  REINKE_CODE,
  "FIND.LARYNX.GRANULOMA",
  "FIND.LARYNX.PAPILLOMA",
  "FIND.LARYNX.LEUKOPLAKIA",
  "FIND.LARYNX.ERYTHROPLAKIA",
  "FIND.LARYNX.ULCER",
  "FIND.LARYNX.MASS",
  "FIND.LARYNX.SULCUS",
  "FIND.LARYNX.SCAR",
  "FIND.LARYNX.WEB",
  "FIND.LARYNX.VARIX",
  "FIND.LARYNX.HEMORRHAGE",
] as const;

export const VF_THIRDS = [
  "QUAL.VF.THIRD.ANTERIOR",
  "QUAL.VF.THIRD.MIDDLE",
  "QUAL.VF.THIRD.POSTERIOR",
] as const;

export const VF_SURFACES = [
  "QUAL.VF.SURFACE.FREE_EDGE",
  "QUAL.VF.SURFACE.SUPERIOR",
] as const;

export const SCOPE_TYPES = [
  "flexible_fiberoptic",
  "flexible_distal_chip",
  "rigid_70",
  "rigid_90",
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

export const MOBILITY_VALUES = [
  "normal",
  "hypomobile",
  "immobile",
  "paradoxical",
] as const;

export const POSITION_VALUES = [
  "median",
  "paramedian",
  "intermediate",
  "lateral",
] as const;

export const GLOTTIC_VALUES = [
  "complete",
  "anterior_gap",
  "posterior_gap",
  "spindle",
  "hourglass",
  "irregular",
  "incomplete",
] as const;

export const SUPRAGLOTTIC_VALUES = [
  "none",
  "anteroposterior",
  "mediolateral",
  "sphincteric",
] as const;

export const STRUCTURE_STATUSES = [
  "unset",
  "normal",
  "abnormal",
  "not_examined",
  "unknown",
] as const;

export const RFS_ITEMS = [
  "subglotticEdema",
  "ventricularObliteration",
  "erythema",
  "vocalFoldEdema",
  "diffuseLaryngealEdema",
  "posteriorCommissureHypertrophy",
  "granuloma",
  "thickEndolaryngealMucus",
] as const;

/** Allowed ordinals from engines.laryngoscopy.reflux_finding_score.ALLOWED. */
export const RFS_CHOICES: Record<RfsItem, readonly number[]> = {
  subglotticEdema: [0, 2],
  ventricularObliteration: [0, 2, 4],
  erythema: [0, 2, 4],
  vocalFoldEdema: [0, 1, 2, 3, 4],
  diffuseLaryngealEdema: [0, 1, 2, 3, 4],
  posteriorCommissureHypertrophy: [0, 1, 2, 3, 4],
  granuloma: [0, 2],
  thickEndolaryngealMucus: [0, 2],
};

export const GRBAS_ITEMS = [
  "grade",
  "roughness",
  "breathiness",
  "asthenia",
  "strain",
] as const;

export const GRBAS_CHOICES = [0, 1, 2, 3] as const;
export const PAS_MIN = 1;
export const PAS_MAX = 8;
export const VIDEO_MAX_MS = 15_000;
export const REINKE_GRADES = [1, 2, 3] as const;

export type LaryngoscopyTemplate =
  | "pre_thyroid"
  | "post_thyroid"
  | "paralysis"
  | "fees"
  | "pediatric"
  | "tracheostomy";
export type StructureStatus = (typeof STRUCTURE_STATUSES)[number];
export type StructureLaterality = "right" | "left" | "midline";
export type RfsItem = (typeof RFS_ITEMS)[number];
export type GrbasItem = (typeof GRBAS_ITEMS)[number];
export type DraftIssue =
  | "finding"
  | "performedAt"
  | "position"
  | "reinke"
  | "rfs"
  | "grbas"
  | "fees"
  | "strobe";

export type StructureDraft = {
  bodySiteCode: string;
  laterality: StructureLaterality;
  status: StructureStatus;
  findingCode: string | null;
};

export type LesionDraft = {
  laterality: "right" | "left";
  thirdCode: string;
  surfaceCode: string;
  findingCode: string;
  sizeMm: number | null;
  reinkeGrade: number | null;
};

export type FoldDraft = {
  mobility: (typeof MOBILITY_VALUES)[number];
  position: "" | (typeof POSITION_VALUES)[number];
};

export type RfsDraft = Record<RfsItem, number | null>;
export type GrbasDraft = Record<GrbasItem, number | null>;

export const PHASE_CLOSURE_VALUES = [
  "normal",
  "predominantly_open",
  "predominantly_closed",
  "always_open",
] as const;

export const VERTICAL_LEVEL_VALUES = [
  "on_plane",
  "off_plane_right_lower",
  "off_plane_left_lower",
] as const;

export const NON_VIBRATING_VALUES = [
  "none",
  "right",
  "left",
  "bilateral",
] as const;

export type StrobeDraft = {
  symmetry: "symmetric" | "asymmetric";
  periodicity: "regular" | "irregular";
  amplitudeRight: "normal" | "reduced" | "absent";
  amplitudeLeft: "normal" | "reduced" | "absent";
  mucosalWaveRight: "normal" | "reduced" | "absent";
  mucosalWaveLeft: "normal" | "reduced" | "absent";
  phaseClosure: "" | (typeof PHASE_CLOSURE_VALUES)[number];
  phaseSymmetry: "" | "symmetric" | "asymmetric";
  verticalLevel: "" | (typeof VERTICAL_LEVEL_VALUES)[number];
  nonVibratingSegment: "" | (typeof NON_VIBRATING_VALUES)[number];
};

export type LaryngoscopyDraft = {
  performedAt: string;
  laterality: (typeof PROCEDURE_LATERALITIES)[number];
  anesthesia: (typeof ANESTHESIA_TYPES)[number];
  setting: (typeof SETTINGS)[number];
  scopeType: (typeof SCOPE_TYPES)[number];
  instrument: string;
  indicationText: string;
  tolerance: "" | (typeof TOLERANCE_VALUES)[number];
  conclusionText: string;
  vocalFoldRight: FoldDraft;
  vocalFoldLeft: FoldDraft;
  glotticClosure: (typeof GLOTTIC_VALUES)[number];
  supraglotticPattern: "" | (typeof SUPRAGLOTTIC_VALUES)[number];
  includeStroboscopy: boolean;
  stroboscopy: StrobeDraft;
  includeRfs: boolean;
  rfs: RfsDraft;
  includeGrbas: boolean;
  grbas: GrbasDraft;
  includeFees: boolean;
  pasScore: number | null;
  consistencies: string[];
  residueSiteCodes: string[];
  structures: StructureDraft[];
  lesions: LesionDraft[];
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
  rfsScore: number | null;
  grbasTotal: number | null;
  pasScore: number | null;
  rfsChanged: boolean;
};

type WriteBody = Omit<LaryngoscopyCreate, "patientPublicId">;

const PRE_THYROID_SITES = new Set([VOCAL_FOLD_CODE, "ANAT.LARYNX.ARYTENOID"]);
const PARALYSIS_SITES = new Set([VOCAL_FOLD_CODE, "ANAT.LARYNX.ARYTENOID"]);
const FEES_SITES = new Set([
  "ANAT.LARYNX.VALLECULA",
  "ANAT.LARYNX.PYRIFORM",
  "ANAT.LARYNX.POST_CRICOID",
  VOCAL_FOLD_CODE,
  "ANAT.LARYNX.EPIGLOTTIS",
]);
const PEDIATRIC_SITES = new Set([
  "ANAT.LARYNX.EPIGLOTTIS",
  "ANAT.LARYNX.VALLECULA",
  "ANAT.LARYNX.SUBGLOTTIS",
  "ANAT.LARYNX.TRACHEA",
]);
const TRACHEOSTOMY_SITES = new Set([
  "ANAT.LARYNX.TRACHEA",
  "ANAT.LARYNX.SUBGLOTTIS",
]);

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
  for (const region of larynxMap.regions) {
    if (region.fixedLaterality === "midline") {
      rows.push(blankStructure(region.bodySiteCode, "midline", status));
      continue;
    }
    rows.push(blankStructure(region.bodySiteCode, "right", status));
    rows.push(blankStructure(region.bodySiteCode, "left", status));
  }
  return rows;
}

function blankRfs(): RfsDraft {
  return {
    subglotticEdema: null,
    ventricularObliteration: null,
    erythema: null,
    vocalFoldEdema: null,
    diffuseLaryngealEdema: null,
    posteriorCommissureHypertrophy: null,
    granuloma: null,
    thickEndolaryngealMucus: null,
  };
}

function blankGrbas(): GrbasDraft {
  return {
    grade: null,
    roughness: null,
    breathiness: null,
    asthenia: null,
    strain: null,
  };
}

function blankStrobe(): StrobeDraft {
  return {
    symmetry: "symmetric",
    periodicity: "regular",
    amplitudeRight: "normal",
    amplitudeLeft: "normal",
    mucosalWaveRight: "normal",
    mucosalWaveLeft: "normal",
    phaseClosure: "",
    phaseSymmetry: "",
    verticalLevel: "",
    nonVibratingSegment: "",
  };
}

function blankFold(): FoldDraft {
  return { mobility: "normal", position: "" };
}

export function emptyDraft(performedAt: string): LaryngoscopyDraft {
  return {
    performedAt,
    laterality: "bilateral",
    anesthesia: "topical_spray",
    setting: "office",
    scopeType: "flexible_fiberoptic",
    instrument: "",
    indicationText: "",
    tolerance: "",
    conclusionText: "",
    vocalFoldRight: blankFold(),
    vocalFoldLeft: blankFold(),
    glotticClosure: "complete",
    supraglotticPattern: "",
    includeStroboscopy: false,
    stroboscopy: blankStrobe(),
    includeRfs: false,
    rfs: blankRfs(),
    includeGrbas: false,
    grbas: blankGrbas(),
    includeFees: false,
    pasScore: null,
    consistencies: [],
    residueSiteCodes: [],
    structures: structureSlots(),
    lesions: [],
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

function focusSites(template: LaryngoscopyTemplate): Set<string> {
  switch (template) {
    case "pre_thyroid":
    case "post_thyroid":
      return PRE_THYROID_SITES;
    case "paralysis":
      return PARALYSIS_SITES;
    case "fees":
      return FEES_SITES;
    case "pediatric":
      return PEDIATRIC_SITES;
    case "tracheostomy":
      return TRACHEOSTOMY_SITES;
    default: {
      const _exhaustive: never = template;
      return _exhaustive;
    }
  }
}

export function applyTemplate(
  draft: LaryngoscopyDraft,
  template: LaryngoscopyTemplate,
): LaryngoscopyDraft {
  const sites = focusSites(template);
  const next: LaryngoscopyDraft = {
    ...draft,
    tolerance: draft.tolerance || "well_tolerated",
    scopeType: "flexible_fiberoptic",
    structures: structureSlots("not_examined").map((row) =>
      sites.has(row.bodySiteCode)
        ? blankStructure(row.bodySiteCode, row.laterality, "unset")
        : row,
    ),
    includeFees: template === "fees" ? true : draft.includeFees,
  };
  if (template === "pre_thyroid" || template === "post_thyroid") {
    return {
      ...next,
      vocalFoldRight: { mobility: "normal", position: "" },
      vocalFoldLeft: { mobility: "normal", position: "" },
      glotticClosure: "complete",
    };
  }
  return next;
}

export function templateFocus(template: LaryngoscopyTemplate): string {
  switch (template) {
    case "pre_thyroid":
    case "post_thyroid":
    case "paralysis":
      return "larynx.vocal-fold";
    case "fees":
      return "larynx.vallecula";
    case "pediatric":
      return "larynx.epiglottis";
    case "tracheostomy":
      return "larynx.trachea";
    default: {
      const _exhaustive: never = template;
      return _exhaustive;
    }
  }
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

function pick<T extends string>(
  options: readonly T[],
  value: string | null | undefined,
): T | undefined {
  return options.find((item) => item === value);
}

function foldFromExam(fold: LaryngoscopyExamRead["vocalFoldRight"]): FoldDraft {
  const mobility = pick(MOBILITY_VALUES, fold.mobility) ?? "normal";
  const position = pick(POSITION_VALUES, fold.position ?? "") ?? "";
  return { mobility, position };
}

function rfsFromExam(exam: LaryngoscopyExamRead): RfsDraft {
  const source = exam.refluxFindingScore;
  if (!source) {
    return blankRfs();
  }
  return {
    subglotticEdema: source.subglotticEdema,
    ventricularObliteration: source.ventricularObliteration,
    erythema: source.erythema,
    vocalFoldEdema: source.vocalFoldEdema,
    diffuseLaryngealEdema: source.diffuseLaryngealEdema,
    posteriorCommissureHypertrophy: source.posteriorCommissureHypertrophy,
    granuloma: source.granuloma,
    thickEndolaryngealMucus: source.thickEndolaryngealMucus,
  };
}

function lesionFromRead(row: VocalFoldLesionRead): LesionDraft | null {
  if (row.laterality !== "right" && row.laterality !== "left") {
    return null;
  }
  if (!row.third.code || !row.surface.code || !row.finding.code) {
    return null;
  }
  return {
    laterality: row.laterality,
    thirdCode: row.third.code,
    surfaceCode: row.surface.code,
    findingCode: row.finding.code,
    sizeMm: row.sizeMm,
    reinkeGrade: row.reinkeGrade,
  };
}

export function draftFromExam(
  exam: LaryngoscopyExamRead,
  performedAt: string,
): LaryngoscopyDraft {
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
  return {
    ...base,
    performedAt,
    laterality: pick(PROCEDURE_LATERALITIES, exam.laterality) ?? "bilateral",
    anesthesia: pick(ANESTHESIA_TYPES, exam.anesthesia) ?? "topical_spray",
    setting: pick(SETTINGS, exam.setting) ?? "office",
    scopeType: pick(SCOPE_TYPES, exam.scopeType) ?? "flexible_fiberoptic",
    instrument: exam.instrument ?? "",
    indicationText: exam.indicationText ?? "",
    tolerance: pick(TOLERANCE_VALUES, exam.tolerance ?? "") ?? "",
    conclusionText: exam.conclusionText ?? "",
    vocalFoldRight: foldFromExam(exam.vocalFoldRight),
    vocalFoldLeft: foldFromExam(exam.vocalFoldLeft),
    glotticClosure: pick(GLOTTIC_VALUES, exam.glotticClosure) ?? "complete",
    supraglotticPattern:
      pick(SUPRAGLOTTIC_VALUES, exam.supraglotticPattern ?? "") ?? "",
    includeStroboscopy: exam.stroboscopyPerformed,
    stroboscopy: {
      symmetry: exam.symmetry === "asymmetric" ? "asymmetric" : "symmetric",
      periodicity: exam.periodicity === "irregular" ? "irregular" : "regular",
      amplitudeRight:
        exam.amplitudeRight === "reduced" || exam.amplitudeRight === "absent"
          ? exam.amplitudeRight
          : "normal",
      amplitudeLeft:
        exam.amplitudeLeft === "reduced" || exam.amplitudeLeft === "absent"
          ? exam.amplitudeLeft
          : "normal",
      mucosalWaveRight:
        exam.mucosalWaveRight === "reduced" ||
        exam.mucosalWaveRight === "absent"
          ? exam.mucosalWaveRight
          : "normal",
      mucosalWaveLeft:
        exam.mucosalWaveLeft === "reduced" || exam.mucosalWaveLeft === "absent"
          ? exam.mucosalWaveLeft
          : "normal",
      phaseClosure: pick(PHASE_CLOSURE_VALUES, exam.phaseClosure ?? "") ?? "",
      phaseSymmetry:
        exam.phaseSymmetry === "symmetric" ||
        exam.phaseSymmetry === "asymmetric"
          ? exam.phaseSymmetry
          : "",
      verticalLevel:
        pick(VERTICAL_LEVEL_VALUES, exam.verticalLevel ?? "") ?? "",
      nonVibratingSegment:
        pick(NON_VIBRATING_VALUES, exam.nonVibratingSegment ?? "") ?? "",
    },
    includeRfs: exam.refluxFindingScore !== null,
    rfs: rfsFromExam(exam),
    includeGrbas: exam.grbas !== null,
    grbas: exam.grbas
      ? {
          grade: exam.grbas.grade,
          roughness: exam.grbas.roughness,
          breathiness: exam.grbas.breathiness,
          asthenia: exam.grbas.asthenia,
          strain: exam.grbas.strain,
        }
      : blankGrbas(),
    includeFees: exam.feesPerformed,
    pasScore: exam.pasScore,
    consistencies: exam.consistencies
      .map((item) => item.code)
      .filter((code): code is string => Boolean(code)),
    residueSiteCodes: exam.residueSites
      .map((item) => item.code)
      .filter((code): code is string => Boolean(code)),
    structures: slots,
    lesions: exam.lesions
      .map(lesionFromRead)
      .filter((row): row is LesionDraft => row !== null),
  };
}

export function withStructureStatus(
  draft: LaryngoscopyDraft,
  bodySiteCode: string,
  laterality: StructureLaterality,
  status: StructureStatus,
): LaryngoscopyDraft {
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
  draft: LaryngoscopyDraft,
  bodySiteCode: string,
  laterality: StructureLaterality,
  findingCode: string,
): LaryngoscopyDraft {
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

export function marksForSide(
  draft: LaryngoscopyDraft,
  side: MapSide,
): Record<string, RegionMark> {
  const marks: Record<string, RegionMark> = {};
  for (const region of larynxMap.regions) {
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
  draft: LaryngoscopyDraft,
  region: MapRegionDefinition,
  side: MapSide,
  findingCode: string,
): LaryngoscopyDraft {
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
  draft: LaryngoscopyDraft,
  region: MapRegionDefinition,
  side: MapSide,
): LaryngoscopyDraft {
  return applyMapFinding(draft, region, side, region.defaultNormalCode);
}

export function applyMapNotExamined(
  draft: LaryngoscopyDraft,
  region: MapRegionDefinition,
  side: MapSide,
): LaryngoscopyDraft {
  return applyMapFinding(draft, region, side, FINDING_NOT_VISUALIZED);
}

function foldWrite(fold: FoldDraft): VocalFoldWrite {
  return {
    mobility: fold.mobility,
    position: fold.mobility === "immobile" ? fold.position || null : null,
  };
}

function rfsWrite(draft: RfsDraft): RefluxFindingScoreWrite | null {
  const complete = RFS_ITEMS.every((item) => {
    const value = draft[item];
    return value !== null && RFS_CHOICES[item].includes(value);
  });
  if (!complete) {
    return null;
  }
  return {
    subglotticEdema: draft.subglotticEdema ?? 0,
    ventricularObliteration: draft.ventricularObliteration ?? 0,
    erythema: draft.erythema ?? 0,
    vocalFoldEdema: draft.vocalFoldEdema ?? 0,
    diffuseLaryngealEdema: draft.diffuseLaryngealEdema ?? 0,
    posteriorCommissureHypertrophy: draft.posteriorCommissureHypertrophy ?? 0,
    granuloma: draft.granuloma ?? 0,
    thickEndolaryngealMucus: draft.thickEndolaryngealMucus ?? 0,
  };
}

function grbasWrite(draft: GrbasDraft): GrbasWrite | null {
  const complete = GRBAS_ITEMS.every((item) => {
    const value = draft[item];
    return (
      value !== null && (GRBAS_CHOICES as readonly number[]).includes(value)
    );
  });
  if (!complete) {
    return null;
  }
  return {
    grade: draft.grade ?? 0,
    roughness: draft.roughness ?? 0,
    breathiness: draft.breathiness ?? 0,
    asthenia: draft.asthenia ?? 0,
    strain: draft.strain ?? 0,
  };
}

function strobeWrite(draft: StrobeDraft): StroboscopyWrite {
  return {
    symmetry: draft.symmetry,
    periodicity: draft.periodicity,
    amplitudeRight: draft.amplitudeRight,
    amplitudeLeft: draft.amplitudeLeft,
    mucosalWaveRight: draft.mucosalWaveRight,
    mucosalWaveLeft: draft.mucosalWaveLeft,
    phaseClosure: draft.phaseClosure === "" ? null : draft.phaseClosure,
    phaseSymmetry: draft.phaseSymmetry === "" ? null : draft.phaseSymmetry,
    verticalLevel: draft.verticalLevel === "" ? null : draft.verticalLevel,
    nonVibratingSegment:
      draft.nonVibratingSegment === "" ? null : draft.nonVibratingSegment,
  };
}

function recordedStructures(
  draft: LaryngoscopyDraft,
): LaryngoscopyStructureWrite[] {
  const rows: LaryngoscopyStructureWrite[] = [];
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

function recordedLesions(draft: LaryngoscopyDraft): VocalFoldLesionWrite[] {
  return draft.lesions.map((lesion) => ({
    laterality: lesion.laterality,
    thirdCode: lesion.thirdCode,
    surfaceCode: lesion.surfaceCode,
    findingCode: lesion.findingCode,
    sizeMm: lesion.sizeMm,
    reinkeGrade: lesion.findingCode === REINKE_CODE ? lesion.reinkeGrade : null,
  }));
}

export function draftIssue(
  draft: LaryngoscopyDraft,
  performedAtIso: string | null,
): DraftIssue | null {
  if (!performedAtIso) {
    return "performedAt";
  }
  for (const fold of [draft.vocalFoldRight, draft.vocalFoldLeft]) {
    if (fold.mobility === "immobile" && fold.position === "") {
      return "position";
    }
    if (fold.mobility !== "immobile" && fold.position !== "") {
      return "position";
    }
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
  for (const lesion of draft.lesions) {
    if (!(LESION_FINDINGS as readonly string[]).includes(lesion.findingCode)) {
      return "finding";
    }
    if (lesion.findingCode === REINKE_CODE && lesion.reinkeGrade === null) {
      return "reinke";
    }
    if (lesion.findingCode !== REINKE_CODE && lesion.reinkeGrade !== null) {
      return "reinke";
    }
  }
  if (draft.includeRfs && rfsWrite(draft.rfs) === null) {
    return "rfs";
  }
  if (draft.includeGrbas && grbasWrite(draft.grbas) === null) {
    return "grbas";
  }
  if (draft.includeFees) {
    if (
      draft.pasScore === null ||
      draft.pasScore < PAS_MIN ||
      draft.pasScore > PAS_MAX ||
      draft.consistencies.length === 0
    ) {
      return "fees";
    }
  }
  return null;
}

export function toWriteBody(
  draft: LaryngoscopyDraft,
  performedAtIso: string | null,
): { ok: true; body: WriteBody } | { ok: false; issue: DraftIssue } {
  const issue = draftIssue(draft, performedAtIso);
  if (issue || !performedAtIso) {
    return { ok: false, issue: issue ?? "performedAt" };
  }
  const fees: FeesWrite | null = draft.includeFees
    ? {
        pasScore: draft.pasScore ?? PAS_MIN,
        consistencies: draft.consistencies,
        residueSiteCodes: draft.residueSiteCodes,
      }
    : null;
  return {
    ok: true,
    body: {
      performedAt: performedAtIso,
      laterality: draft.laterality,
      anesthesia: draft.anesthesia,
      setting: draft.setting,
      scopeType: draft.scopeType,
      instrument: draft.instrument.trim() || null,
      indicationText: draft.indicationText.trim() || null,
      tolerance: draft.tolerance || null,
      conclusionText: draft.conclusionText.trim() || null,
      vocalFoldRight: foldWrite(draft.vocalFoldRight),
      vocalFoldLeft: foldWrite(draft.vocalFoldLeft),
      glotticClosure: draft.glotticClosure,
      supraglotticPattern: draft.supraglotticPattern || null,
      structures: recordedStructures(draft),
      lesions: recordedLesions(draft),
      stroboscopy: draft.includeStroboscopy
        ? strobeWrite(draft.stroboscopy)
        : null,
      refluxFindingScore: draft.includeRfs ? rfsWrite(draft.rfs) : null,
      grbas: draft.includeGrbas ? grbasWrite(draft.grbas) : null,
      fees,
    },
  };
}

export function toCreateBody(
  draft: LaryngoscopyDraft,
  patientId: string,
  performedAtIso: string | null,
): { ok: true; body: LaryngoscopyCreate } | { ok: false; issue: DraftIssue } {
  const written = toWriteBody(draft, performedAtIso);
  if (!written.ok) {
    return written;
  }
  return { ok: true, body: { ...written.body, patientPublicId: patientId } };
}

export function toUpdateBody(
  draft: LaryngoscopyDraft,
  version: number,
  performedAtIso: string | null,
): { ok: true; body: LaryngoscopyUpdate } | { ok: false; issue: DraftIssue } {
  const written = toWriteBody(draft, performedAtIso);
  if (!written.ok) {
    return written;
  }
  return { ok: true, body: { ...written.body, version } };
}

function structureDisplay(row: LaryngoscopyStructureRead): string | null {
  return row.finding.display ?? row.finding.code ?? null;
}

export function compareStructures(
  current: readonly StructureDraft[],
  previous: readonly LaryngoscopyStructureRead[],
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
  if (older.length === 0) {
    return null;
  }
  return (
    [...older].sort(
      (left, right) =>
        occurredAt(right.performedAt) - occurredAt(left.performedAt),
    )[0] ?? null
  );
}

export function scoreTrend(
  exams: readonly LaryngoscopyExamRead[],
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
      rfsScore: exam.rfsScore,
      grbasTotal: exam.grbas?.total ?? null,
      pasScore: exam.pasScore,
      rfsChanged: prior !== null && prior.rfsScore !== exam.rfsScore,
    };
  });
}

export function regionBySite(bodySiteCode: string): MapRegionDefinition | null {
  return (
    larynxMap.regions.find((region) => region.bodySiteCode === bodySiteCode) ??
    null
  );
}
