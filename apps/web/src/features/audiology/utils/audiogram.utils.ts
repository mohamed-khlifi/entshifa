/**
 * Audiogram chart layout and symbol helpers — display only, no clinical math.
 */

import type { ThresholdInput, ThresholdRead } from "@/lib/api/generated";

import {
  BONE_FREQUENCIES_HZ,
  CHART_DB_TICKS,
  CHART_HEIGHT,
  CHART_PADDING,
  CHART_WIDTH,
  EXTENDED_HIGH_FREQUENCIES_HZ,
  LEVEL_STEP_DB,
  MAX_LEVEL_DB,
  MIN_LEVEL_DB,
  STANDARD_FREQUENCIES_HZ,
} from "../constants";
import type {
  ActivePlotMode,
  AudiogramConduction,
  AudiogramEar,
  ThresholdCell,
} from "../types/audiology.types";

const REF_HZ = 125;

export function cellKey(
  ear: AudiogramEar,
  conduction: AudiogramConduction,
  isMasked: boolean,
  frequencyHz: number,
): string {
  return `${ear}:${conduction}:${isMasked ? "1" : "0"}:${frequencyHz}`;
}

export function parseCellKey(key: string): {
  ear: AudiogramEar;
  conduction: AudiogramConduction;
  isMasked: boolean;
  frequencyHz: number;
} {
  const [ear, conduction, masked, freq] = key.split(":");
  return {
    ear: ear as AudiogramEar,
    conduction: conduction as AudiogramConduction,
    isMasked: masked === "1",
    frequencyHz: Number(freq),
  };
}

export function frequenciesForChart(showExtendedHigh: boolean): number[] {
  return showExtendedHigh
    ? [...STANDARD_FREQUENCIES_HZ, ...EXTENDED_HIGH_FREQUENCIES_HZ]
    : [...STANDARD_FREQUENCIES_HZ];
}

export function frequencyAllowed(
  frequencyHz: number,
  conduction: AudiogramConduction,
  showExtendedHigh: boolean,
): boolean {
  const allowed = frequenciesForChart(showExtendedHigh);
  if (!allowed.includes(frequencyHz)) {
    return false;
  }
  if (conduction === "bone") {
    return (BONE_FREQUENCIES_HZ as readonly number[]).includes(frequencyHz);
  }
  return true;
}

export function plotInnerSize(): { width: number; height: number } {
  return {
    width: CHART_WIDTH - CHART_PADDING.left - CHART_PADDING.right,
    height: CHART_HEIGHT - CHART_PADDING.top - CHART_PADDING.bottom,
  };
}

function logPosition(
  frequencyHz: number,
  minHz: number,
  maxHz: number,
): number {
  const minLog = Math.log2(minHz / REF_HZ);
  const maxLog = Math.log2(maxHz / REF_HZ);
  const valueLog = Math.log2(frequencyHz / REF_HZ);
  if (maxLog === minLog) {
    return 0;
  }
  return (valueLog - minLog) / (maxLog - minLog);
}

export function frequencyToX(
  frequencyHz: number,
  frequencies: readonly number[],
): number {
  const { width } = plotInnerSize();
  const minHz = frequencies[0] ?? REF_HZ;
  const maxHz = frequencies[frequencies.length - 1] ?? 8000;
  return CHART_PADDING.left + logPosition(frequencyHz, minHz, maxHz) * width;
}

export function xToFrequencyHz(
  x: number,
  frequencies: readonly number[],
): number {
  const { width } = plotInnerSize();
  const minHz = frequencies[0] ?? REF_HZ;
  const maxHz = frequencies[frequencies.length - 1] ?? 8000;
  const ratio = Math.min(1, Math.max(0, (x - CHART_PADDING.left) / width));
  const minLog = Math.log2(minHz / REF_HZ);
  const maxLog = Math.log2(maxHz / REF_HZ);
  const targetLog = minLog + ratio * (maxLog - minLog);
  const rawHz = REF_HZ * 2 ** targetLog;
  return snapToNearestFrequency(rawHz, frequencies);
}

export function snapToNearestFrequency(
  rawHz: number,
  frequencies: readonly number[],
): number {
  let best = frequencies[0] ?? REF_HZ;
  let bestDistance = Number.POSITIVE_INFINITY;
  for (const hz of frequencies) {
    const distance = Math.abs(Math.log2(rawHz / hz));
    if (distance < bestDistance) {
      bestDistance = distance;
      best = hz;
    }
  }
  return best;
}

export function levelDbToY(levelDb: number): number {
  const { height } = plotInnerSize();
  const ratio = (levelDb - MIN_LEVEL_DB) / (MAX_LEVEL_DB - MIN_LEVEL_DB);
  return CHART_PADDING.top + ratio * height;
}

export function yToLevelDb(y: number): number {
  const { height } = plotInnerSize();
  const ratio = Math.min(1, Math.max(0, (y - CHART_PADDING.top) / height));
  const raw = MIN_LEVEL_DB + ratio * (MAX_LEVEL_DB - MIN_LEVEL_DB);
  return snapLevelDb(raw);
}

export function snapLevelDb(raw: number): number {
  const snapped =
    Math.round((raw - MIN_LEVEL_DB) / LEVEL_STEP_DB) * LEVEL_STEP_DB +
    MIN_LEVEL_DB;
  return Math.min(MAX_LEVEL_DB, Math.max(MIN_LEVEL_DB, snapped));
}

export function chartDbTicks(): readonly number[] {
  return CHART_DB_TICKS;
}

export type SymbolDescriptor = {
  ear: AudiogramEar;
  conduction: AudiogramConduction;
  isMasked: boolean;
  isNoResponse: boolean;
};

export function resolveSymbolDescriptor(
  ear: AudiogramEar,
  conduction: AudiogramConduction,
  isMasked: boolean,
  isNoResponse: boolean,
): SymbolDescriptor {
  return { ear, conduction, isMasked, isNoResponse };
}

export function earColor(ear: AudiogramEar): string {
  return ear === "right" ? "#dc2626" : "#2563eb";
}

export type ChartPoint = {
  frequencyHz: number;
  levelDb: number;
  ear: AudiogramEar;
  conduction: AudiogramConduction;
  isMasked: boolean;
  isNoResponse: boolean;
};

export function thresholdsToChartPoints(
  thresholds: readonly (ThresholdRead | ThresholdInput)[],
): ChartPoint[] {
  return thresholds
    .filter((row) => row.levelDb !== null && row.levelDb !== undefined)
    .map((row) => ({
      frequencyHz: row.frequencyHz,
      levelDb: row.levelDb as number,
      ear: row.ear as AudiogramEar,
      conduction: row.conduction as AudiogramConduction,
      isMasked: row.isMasked,
      isNoResponse: row.isNoResponse,
    }));
}

export function connectablePoints(
  points: ChartPoint[],
  ear: AudiogramEar,
  conduction: AudiogramConduction,
  isMasked: boolean,
): ChartPoint[] {
  return points
    .filter(
      (point) =>
        point.ear === ear &&
        point.conduction === conduction &&
        point.isMasked === isMasked &&
        !point.isNoResponse,
    )
    .sort((a, b) => a.frequencyHz - b.frequencyHz);
}

export function cellsFromThresholds(
  thresholds: readonly ThresholdRead[],
): Record<string, ThresholdCell> {
  const cells: Record<string, ThresholdCell> = {};
  for (const row of thresholds) {
    const key = cellKey(
      row.ear as AudiogramEar,
      row.conduction as AudiogramConduction,
      row.isMasked,
      row.frequencyHz,
    );
    cells[key] = {
      levelDb: row.levelDb,
      isNoResponse: row.isNoResponse,
    };
  }
  return cells;
}

export function thresholdsFromCells(
  cells: Record<string, ThresholdCell>,
): ThresholdInput[] {
  const rows: ThresholdInput[] = [];
  for (const [key, cell] of Object.entries(cells)) {
    if (cell.levelDb === null && !cell.isNoResponse) {
      continue;
    }
    const parsed = parseCellKey(key);
    rows.push({
      ear: parsed.ear,
      conduction: parsed.conduction,
      frequencyHz: parsed.frequencyHz,
      levelDb: cell.isNoResponse ? cell.levelDb : cell.levelDb,
      isMasked: parsed.isMasked,
      isNoResponse: cell.isNoResponse,
    });
  }
  return rows.sort(
    (a, b) =>
      a.ear.localeCompare(b.ear) ||
      a.conduction.localeCompare(b.conduction) ||
      Number(a.isMasked) - Number(b.isMasked) ||
      a.frequencyHz - b.frequencyHz,
  );
}

export function setCellValue(
  cells: Record<string, ThresholdCell>,
  mode: ActivePlotMode,
  frequencyHz: number,
  levelDb: number | null,
  isNoResponse = false,
): Record<string, ThresholdCell> {
  const key = cellKey(mode.ear, mode.conduction, mode.isMasked, frequencyHz);
  if (levelDb === null && !isNoResponse) {
    const next = { ...cells };
    delete next[key];
    return next;
  }
  return {
    ...cells,
    [key]: {
      levelDb: isNoResponse ? (levelDb ?? MAX_LEVEL_DB) : levelDb,
      isNoResponse,
    },
  };
}

export function toggleNoResponse(
  cells: Record<string, ThresholdCell>,
  mode: ActivePlotMode,
  frequencyHz: number,
): Record<string, ThresholdCell> {
  const key = cellKey(mode.ear, mode.conduction, mode.isMasked, frequencyHz);
  const current = cells[key];
  if (!current) {
    return setCellValue(cells, mode, frequencyHz, MAX_LEVEL_DB, true);
  }
  if (current.isNoResponse) {
    return setCellValue(cells, mode, frequencyHz, current.levelDb, false);
  }
  return setCellValue(
    cells,
    mode,
    frequencyHz,
    current.levelDb ?? MAX_LEVEL_DB,
    true,
  );
}

export function hasExtendedHighFrequencies(
  thresholds: readonly ThresholdRead[],
): boolean {
  return thresholds.some((row) =>
    (EXTENDED_HIGH_FREQUENCIES_HZ as readonly number[]).includes(
      row.frequencyHz,
    ),
  );
}
