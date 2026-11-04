import type { AudiogramRead, ThresholdRead } from "@/lib/api/generated";

import {
  CONDUCTIONS,
  EARS,
  RELIABILITY_VALUES,
  TEST_METHODS,
  TRANSDUCERS,
} from "../constants";

export type AudiogramEar = (typeof EARS)[number];
export type AudiogramConduction = (typeof CONDUCTIONS)[number];
export type AudiogramTransducer = (typeof TRANSDUCERS)[number];
export type AudiogramMethod = (typeof TEST_METHODS)[number];
export type AudiogramReliability = (typeof RELIABILITY_VALUES)[number];

export type ThresholdCell = {
  levelDb: number | null;
  isNoResponse: boolean;
};

export type ActivePlotMode = {
  ear: AudiogramEar;
  conduction: AudiogramConduction;
  isMasked: boolean;
};

export type GridFocus = ActivePlotMode & {
  frequencyHz: number;
};

export type PlottedThreshold = ThresholdRead;

export type OverlaySeries = {
  publicId: string;
  performedAt: string;
  isBaseline: boolean;
  thresholds: ThresholdRead[];
};

export type ServerMetricsSnapshot = Pick<
  AudiogramRead,
  | "ptaFormula"
  | "ptaRight"
  | "ptaLeft"
  | "abgRight"
  | "abgLeft"
  | "gradeRight"
  | "gradeLeft"
  | "lossTypeRight"
  | "lossTypeLeft"
  | "configurationRight"
  | "configurationLeft"
  | "asymmetryFlag"
  | "shiftFlag"
>;

export type AudiogramDraft = {
  performedAt: string;
  transducer: AudiogramTransducer;
  method: AudiogramMethod;
  reliability: AudiogramReliability;
  equipment: string;
  calibrationDate: string;
  interpretationText: string;
  isBaseline: boolean;
  showExtendedHigh: boolean;
  isMinimumResponseLevel: boolean;
  cells: Record<string, ThresholdCell>;
  activeMode: ActivePlotMode;
  focusFrequencyHz: number;
  publicId: string | null;
  status: "draft" | "final";
  version: number | null;
  metrics: ServerMetricsSnapshot;
};
