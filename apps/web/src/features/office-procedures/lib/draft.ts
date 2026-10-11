import type {
  OfficeProcedureCreate,
  OfficeProcedureRead,
} from "@/lib/api/generated";
import { dateTimeLocalToUtcIso } from "@/features/attachments";

/**
 * Suggested due dates from feature spec appendix C.
 * The clinician sees the date and can change it before save.
 * 48-72 h, day 7-10, 7-10 days, and 2-4 weeks.
 */
export const SUGGESTED_DAYS = {
  packRemoval: 2,
  splintRemoval: 7,
  specimenReview: 7,
  sialendoscopyVisit: 14,
} as const;

export const SUBTYPES = [
  "epistaxis_management",
  "fine_needle_aspiration",
  "oral_pharyngeal_biopsy",
  "botulinum_injection",
  "peritonsillar_drainage",
  "nasal_fracture_reduction",
  "sialendoscopy",
] as const;

export type OfficeSubtype = (typeof SUBTYPES)[number];

const SIDED = new Set<OfficeSubtype>([
  "epistaxis_management",
  "peritonsillar_drainage",
  "sialendoscopy",
]);

const PACK_METHODS = new Set(["anterior_pack", "posterior_pack", "balloon"]);

export type ContentLocale = "en" | "fr" | "ar";

export type InjectionDraft = {
  muscle: string;
  side: string;
  doseUnits: string;
};

export type OfficeDraft = {
  publicId: string | null;
  version: number | null;
  procedureId: string | null;
  procedureStatus: string;
  procedureDisplay: string;
  performedAt: string;
  laterality: string;
  anesthesia: string;
  tolerance: string;
  subtype: OfficeSubtype;
  siteFound: boolean;
  bleedingSite: string;
  epistaxisMethod: string;
  packType: string;
  packRemovalDate: string;
  systolic: string;
  diastolic: string;
  anticoagulant: string;
  adviceText: string;
  fnaSite: string;
  fnaSiteNote: string;
  needleGauge: string;
  passes: string;
  ultrasoundGuided: boolean;
  laboratoryText: string;
  resultDueDate: string;
  biopsySite: string;
  technique: string;
  indication: string;
  injections: InjectionDraft[];
  drainageMethod: string;
  volumeMl: string;
  cultureSent: boolean;
  splintType: string;
  splintRemovalDate: string;
  gland: string;
  findings: string[];
  stoneRemoved: boolean;
  followUpDate: string;
  noteText: string;
};

export function addCalendarDays(ymd: string, days: number): string {
  const [year, month, day] = ymd.split("-").map(Number);
  if (!year || !month || !day) {
    return "";
  }
  const next = new Date(Date.UTC(year, month - 1, day + days));
  return next.toISOString().slice(0, 10);
}

export function emptyDraft(performedAt: string): OfficeDraft {
  const day = performedAt.slice(0, 10);
  return {
    publicId: null,
    version: null,
    procedureId: null,
    procedureStatus: "draft",
    procedureDisplay: "",
    performedAt,
    laterality: "right",
    anesthesia: "topical_spray",
    tolerance: "",
    subtype: "epistaxis_management",
    siteFound: false,
    bleedingSite: "",
    epistaxisMethod: "silver_nitrate",
    packType: "merocel",
    packRemovalDate: addCalendarDays(day, SUGGESTED_DAYS.packRemoval),
    systolic: "",
    diastolic: "",
    anticoagulant: "unknown",
    adviceText: "",
    fnaSite: "thyroid",
    fnaSiteNote: "",
    needleGauge: "25",
    passes: "2",
    ultrasoundGuided: false,
    laboratoryText: "",
    resultDueDate: addCalendarDays(day, SUGGESTED_DAYS.specimenReview),
    biopsySite: "oral_cavity",
    technique: "punch",
    indication: "sialorrhea",
    injections: [{ muscle: "parotid", side: "right", doseUnits: "" }],
    drainageMethod: "aspiration",
    volumeMl: "",
    cultureSent: false,
    splintType: "thermoplastic",
    splintRemovalDate: addCalendarDays(day, SUGGESTED_DAYS.splintRemoval),
    gland: "submandibular",
    findings: ["stone"],
    stoneRemoved: false,
    followUpDate: addCalendarDays(day, SUGGESTED_DAYS.sialendoscopyVisit),
    noteText: "",
  };
}

export function draftFromRead(
  row: OfficeProcedureRead,
  performedAt: string,
): OfficeDraft {
  const draft = emptyDraft(performedAt);
  draft.publicId = row.publicId;
  draft.version = row.version;
  draft.procedureId = row.procedureId;
  draft.procedureStatus = row.procedureStatus;
  draft.procedureDisplay = row.procedure.display ?? row.procedure.code ?? "";
  draft.laterality = row.laterality;
  draft.anesthesia = row.anesthesia;
  draft.tolerance = row.tolerance ?? "";
  draft.noteText = row.detail.noteText ?? "";
  const detail = row.detail;
  draft.subtype = detail.subtype;
  switch (detail.subtype) {
    case "epistaxis_management":
      draft.siteFound = detail.siteFound;
      draft.bleedingSite = detail.bleedingSite ?? "";
      draft.epistaxisMethod = detail.method;
      draft.packType = detail.packType ?? "merocel";
      draft.packRemovalDate = detail.packRemovalDate ?? "";
      draft.systolic = String(detail.systolicBp);
      draft.diastolic = String(detail.diastolicBp);
      draft.anticoagulant = detail.anticoagulantStatus;
      draft.adviceText = detail.adviceText ?? "";
      break;
    case "fine_needle_aspiration":
      draft.fnaSite = detail.site;
      draft.fnaSiteNote = detail.siteNote ?? "";
      draft.needleGauge = String(detail.needleGauge);
      draft.passes = String(detail.passes);
      draft.ultrasoundGuided = detail.ultrasoundGuided;
      draft.laboratoryText = detail.laboratoryText;
      draft.resultDueDate = detail.resultDueDate;
      break;
    case "oral_pharyngeal_biopsy":
      draft.biopsySite = detail.site;
      draft.technique = detail.technique;
      draft.laboratoryText = detail.laboratoryText;
      draft.resultDueDate = detail.resultDueDate;
      break;
    case "botulinum_injection":
      draft.indication = detail.indication;
      draft.injections = detail.injections.map((item) => ({
        muscle: item.muscle,
        side: item.side,
        doseUnits: item.doseUnits,
      }));
      break;
    case "peritonsillar_drainage":
      draft.drainageMethod = detail.method;
      draft.volumeMl = detail.volumeMl;
      draft.cultureSent = detail.cultureSent;
      break;
    case "nasal_fracture_reduction":
      draft.splintType = detail.splintType;
      draft.splintRemovalDate = detail.splintRemovalDate;
      break;
    case "sialendoscopy":
      draft.gland = detail.gland;
      draft.findings = [...detail.findings];
      draft.stoneRemoved = detail.stoneRemoved;
      draft.followUpDate = detail.followUpDate;
      break;
    default: {
      const unreachable: never = detail;
      return unreachable;
    }
  }
  return draft;
}

export function draftIssues(
  draft: OfficeDraft,
  contentLocale: ContentLocale,
): string[] {
  const issues: string[] = [];
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(draft.performedAt)) {
    issues.push("performedAt");
  }
  if (
    SIDED.has(draft.subtype) &&
    !["right", "left"].includes(draft.laterality)
  ) {
    issues.push("laterality");
  }
  if (draft.noteText.trim() && !contentLocale) {
    issues.push("note");
  }
  switch (draft.subtype) {
    case "epistaxis_management":
      if (!draft.systolic.trim() || !draft.diastolic.trim()) {
        issues.push("bloodPressure");
      }
      if (draft.siteFound && !draft.bleedingSite) {
        issues.push("bleedingSite");
      }
      if (PACK_METHODS.has(draft.epistaxisMethod) && !draft.packRemovalDate) {
        issues.push("packRemoval");
      }
      if (draft.epistaxisMethod === "anterior_pack" && !draft.packType) {
        issues.push("packType");
      }
      if (draft.adviceText.trim() && !contentLocale) {
        issues.push("advice");
      }
      break;
    case "fine_needle_aspiration":
      if (!draft.laboratoryText.trim()) {
        issues.push("laboratory");
      }
      if (!draft.resultDueDate) {
        issues.push("resultDue");
      }
      if (draft.fnaSite === "other" && !draft.fnaSiteNote.trim()) {
        issues.push("siteNote");
      }
      break;
    case "oral_pharyngeal_biopsy":
      if (!draft.laboratoryText.trim()) {
        issues.push("laboratory");
      }
      if (!draft.resultDueDate) {
        issues.push("resultDue");
      }
      break;
    case "botulinum_injection":
      if (draft.injections.length === 0) {
        issues.push("injections");
      }
      if (draft.injections.some((item) => !item.doseUnits.trim())) {
        issues.push("dose");
      }
      break;
    case "peritonsillar_drainage":
      if (!draft.volumeMl.trim()) {
        issues.push("dose");
      }
      break;
    case "nasal_fracture_reduction":
      if (!draft.splintRemovalDate) {
        issues.push("splintRemoval");
      }
      break;
    case "sialendoscopy":
      if (draft.findings.length === 0) {
        issues.push("findings");
      }
      if (!draft.followUpDate) {
        issues.push("followUp");
      }
      break;
    default: {
      const unreachable: never = draft.subtype;
      return [unreachable];
    }
  }
  return issues;
}

function note(draft: OfficeDraft, locale: ContentLocale) {
  const text = draft.noteText.trim();
  if (!text || draft.subtype === "epistaxis_management") {
    return {};
  }
  return { noteText: text, noteLocale: locale };
}

export function toWrite(
  draft: OfficeDraft,
  patientId: string,
  locale: ContentLocale,
  timeZone: string,
): OfficeProcedureCreate | null {
  if (draftIssues(draft, locale).length > 0) {
    return null;
  }
  const performedAt = dateTimeLocalToUtcIso(draft.performedAt, timeZone);
  if (!performedAt) {
    return null;
  }
  const shared = {
    patientPublicId: patientId,
    performedAt,
    laterality: draft.laterality as OfficeProcedureCreate["laterality"],
    anesthesia: draft.anesthesia as OfficeProcedureCreate["anesthesia"],
    tolerance: draft.tolerance
      ? (draft.tolerance as NonNullable<OfficeProcedureCreate["tolerance"]>)
      : null,
  };
  switch (draft.subtype) {
    case "epistaxis_management":
      return {
        ...shared,
        detail: {
          subtype: "epistaxis_management",
          siteFound: draft.siteFound,
          bleedingSite: draft.siteFound
            ? (draft.bleedingSite as "little_area")
            : null,
          method: draft.epistaxisMethod as "silver_nitrate",
          packType:
            draft.epistaxisMethod === "anterior_pack"
              ? (draft.packType as "merocel")
              : null,
          packRemovalDate: PACK_METHODS.has(draft.epistaxisMethod)
            ? draft.packRemovalDate
            : null,
          systolicBp: Number(draft.systolic),
          diastolicBp: Number(draft.diastolic),
          anticoagulantStatus: draft.anticoagulant as "yes",
          adviceText: draft.adviceText.trim() || null,
          adviceLocale: draft.adviceText.trim() ? locale : null,
        },
      };
    case "fine_needle_aspiration":
      return {
        ...shared,
        detail: {
          subtype: "fine_needle_aspiration",
          site: draft.fnaSite as "thyroid",
          siteNote: draft.fnaSite === "other" ? draft.fnaSiteNote.trim() : null,
          siteNoteLocale: draft.fnaSite === "other" ? locale : null,
          needleGauge: Number(draft.needleGauge),
          passes: Number(draft.passes),
          ultrasoundGuided: draft.ultrasoundGuided,
          laboratoryText: draft.laboratoryText.trim(),
          laboratoryLocale: locale,
          resultDueDate: draft.resultDueDate,
          ...note(draft, locale),
        },
      };
    case "oral_pharyngeal_biopsy":
      return {
        ...shared,
        detail: {
          subtype: "oral_pharyngeal_biopsy",
          site: draft.biopsySite as "tongue",
          technique: draft.technique as "punch",
          laboratoryText: draft.laboratoryText.trim(),
          laboratoryLocale: locale,
          resultDueDate: draft.resultDueDate,
          ...note(draft, locale),
        },
      };
    case "botulinum_injection":
      return {
        ...shared,
        detail: {
          subtype: "botulinum_injection",
          indication: draft.indication as "sialorrhea",
          injections: draft.injections.map((item) => ({
            muscle: item.muscle as "parotid",
            side: item.side as "right",
            doseUnits: item.doseUnits,
          })),
          ...note(draft, locale),
        },
      };
    case "peritonsillar_drainage":
      return {
        ...shared,
        detail: {
          subtype: "peritonsillar_drainage",
          method: draft.drainageMethod as "aspiration",
          volumeMl: draft.volumeMl,
          cultureSent: draft.cultureSent,
          ...note(draft, locale),
        },
      };
    case "nasal_fracture_reduction":
      return {
        ...shared,
        detail: {
          subtype: "nasal_fracture_reduction",
          splintType: draft.splintType as "thermoplastic",
          splintRemovalDate: draft.splintRemovalDate,
          ...note(draft, locale),
        },
      };
    case "sialendoscopy":
      return {
        ...shared,
        detail: {
          subtype: "sialendoscopy",
          gland: draft.gland as "parotid",
          findings: draft.findings as "stone"[],
          stoneRemoved: draft.stoneRemoved && draft.findings.includes("stone"),
          followUpDate: draft.followUpDate,
          ...note(draft, locale),
        },
      };
    default: {
      const unreachable: never = draft.subtype;
      return unreachable;
    }
  }
}
