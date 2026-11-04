import { dateTimeLocalToUtcIso } from "@/features/attachments";
import type {
  AudiogramCreate,
  AudiogramRead,
  AudiogramUpdate,
} from "@/lib/api/generated";

import { isoToDateTimeLocal } from "../lib/clock";
import type {
  ActivePlotMode,
  AudiogramDraft,
  ServerMetricsSnapshot,
} from "../types/audiology.types";
import {
  cellsFromThresholds,
  hasExtendedHighFrequencies,
  thresholdsFromCells,
} from "../utils/audiogram.utils";

export type DraftIssue =
  "performedAt" | "duplicateCell" | "invalidLevel" | "invalidFrequency";

export type { AudiogramDraft } from "../types/audiology.types";

export function emptyDraft(performedAt: string): AudiogramDraft {
  return {
    performedAt,
    transducer: "headphones",
    method: "standard",
    reliability: "good",
    equipment: "",
    calibrationDate: "",
    interpretationText: "",
    isBaseline: false,
    showExtendedHigh: false,
    isMinimumResponseLevel: false,
    cells: {},
    activeMode: { ear: "right", conduction: "air", isMasked: false },
    focusFrequencyHz: 1000,
    publicId: null,
    status: "draft",
    version: null,
    metrics: emptyMetrics(),
  };
}

function emptyMetrics(): ServerMetricsSnapshot {
  return {
    ptaFormula: null,
    ptaRight: null,
    ptaLeft: null,
    abgRight: null,
    abgLeft: null,
    gradeRight: null,
    gradeLeft: null,
    lossTypeRight: null,
    lossTypeLeft: null,
    configurationRight: null,
    configurationLeft: null,
    asymmetryFlag: false,
    shiftFlag: false,
  };
}

export function metricsFromRead(exam: AudiogramRead): ServerMetricsSnapshot {
  return {
    ptaFormula: exam.ptaFormula,
    ptaRight: exam.ptaRight,
    ptaLeft: exam.ptaLeft,
    abgRight: exam.abgRight,
    abgLeft: exam.abgLeft,
    gradeRight: exam.gradeRight,
    gradeLeft: exam.gradeLeft,
    lossTypeRight: exam.lossTypeRight,
    lossTypeLeft: exam.lossTypeLeft,
    configurationRight: exam.configurationRight,
    configurationLeft: exam.configurationLeft,
    asymmetryFlag: exam.asymmetryFlag,
    shiftFlag: exam.shiftFlag,
  };
}

export function draftFromExam(
  exam: AudiogramRead,
  performedAtLocal: string,
): AudiogramDraft {
  return {
    performedAt: performedAtLocal,
    transducer: exam.transducer,
    method: exam.method,
    reliability: exam.reliability,
    equipment: exam.equipment ?? "",
    calibrationDate: exam.calibrationDate ?? "",
    interpretationText: exam.interpretationText ?? "",
    isBaseline: exam.isBaseline,
    showExtendedHigh:
      exam.hasExtendedHighFrequencies ||
      hasExtendedHighFrequencies(exam.thresholds),
    isMinimumResponseLevel: Boolean(exam.isMinimumResponseLevel),
    cells: cellsFromThresholds(exam.thresholds),
    activeMode: { ear: "right", conduction: "air", isMasked: false },
    focusFrequencyHz: 1000,
    publicId: exam.publicId,
    status: exam.status === "final" ? "final" : "draft",
    version: exam.version,
    metrics: metricsFromRead(exam),
  };
}

export function draftIssues(draft: AudiogramDraft): DraftIssue[] {
  const issues: DraftIssue[] = [];
  if (!draft.performedAt.trim()) {
    issues.push("performedAt");
  }
  return issues;
}

export function toWrite(
  draft: AudiogramDraft,
  patientId: string,
  timeZone: string,
  options: { canInterpret: boolean },
): {
  create: AudiogramCreate;
  update: AudiogramUpdate;
} | null {
  const performedAt = dateTimeLocalToUtcIso(draft.performedAt, timeZone);
  if (!performedAt) {
    return null;
  }
  const thresholds = thresholdsFromCells(draft.cells);
  const base = {
    performedAt,
    equipment: draft.equipment.trim() || null,
    calibrationDate: draft.calibrationDate.trim() || null,
    transducer: draft.transducer,
    method: draft.method,
    reliability: draft.reliability,
    thresholds,
    isMinimumResponseLevel: draft.isMinimumResponseLevel,
    ...(options.canInterpret
      ? {
          interpretationText: draft.interpretationText.trim() || null,
          isBaseline: draft.isBaseline,
        }
      : {}),
  };
  return {
    create: {
      patientPublicId: patientId,
      isBaseline: options.canInterpret ? draft.isBaseline : false,
      ...base,
    },
    update: {
      version: draft.version ?? 1,
      ...base,
    },
  };
}

export function cycleActiveEar(mode: ActivePlotMode): ActivePlotMode {
  return { ...mode, ear: mode.ear === "right" ? "left" : "right" };
}

export function toggleActiveMasked(mode: ActivePlotMode): ActivePlotMode {
  return { ...mode, isMasked: !mode.isMasked };
}

export function loadDraftFromExam(
  exam: AudiogramRead,
  timeZone: string,
): AudiogramDraft {
  return draftFromExam(exam, isoToDateTimeLocal(exam.performedAt, timeZone));
}
