import type { AudiogramRead } from "@/lib/api/generated";

import type { AudiogramEar, OverlaySeries } from "../types/audiology.types";
import type { ChartPoint } from "./audiogram.utils";

export type EvolutionSample = {
  audiogramPublicId: string;
  performedAt: string;
  rightLevelDb: number | null;
  leftLevelDb: number | null;
  rightNoResponse: boolean;
  leftNoResponse: boolean;
};

export type ThresholdComparisonRow = {
  ear: AudiogramEar;
  frequencyHz: number;
  currentLevelDb: number | null;
  previousLevelDb: number | null;
  currentNoResponse: boolean;
  previousNoResponse: boolean;
};

export function filterPointsByEar(
  points: readonly ChartPoint[],
  ear: AudiogramEar,
): ChartPoint[] {
  return points.filter((point) => point.ear === ear);
}

export function filterOverlaysByEar(
  overlays: readonly OverlaySeries[],
  ear: AudiogramEar,
): OverlaySeries[] {
  return overlays.map((overlay) => ({
    ...overlay,
    thresholds: overlay.thresholds.filter((row) => row.ear === ear),
  }));
}

export function buildFrequencyEvolutionSeries(
  audiograms: readonly AudiogramRead[],
  frequencyHz: number,
  conduction: "air" | "bone" = "air",
  isMasked = false,
): EvolutionSample[] {
  const sorted = [...audiograms].sort(
    (a, b) =>
      new Date(a.performedAt).getTime() - new Date(b.performedAt).getTime(),
  );
  return sorted.map((exam) => {
    const match = (ear: AudiogramEar) =>
      exam.thresholds.find(
        (row) =>
          row.ear === ear &&
          row.conduction === conduction &&
          row.isMasked === isMasked &&
          row.frequencyHz === frequencyHz,
      );
    const right = match("right");
    const left = match("left");
    return {
      audiogramPublicId: exam.publicId,
      performedAt: exam.performedAt,
      rightLevelDb: right?.levelDb ?? null,
      rightNoResponse: right?.isNoResponse ?? false,
      leftLevelDb: left?.levelDb ?? null,
      leftNoResponse: left?.isNoResponse ?? false,
    };
  });
}

export function buildThresholdComparisonRows(
  current: AudiogramRead,
  previous: AudiogramRead,
  frequencies: readonly number[],
): ThresholdComparisonRow[] {
  const rows: ThresholdComparisonRow[] = [];
  for (const ear of ["right", "left"] as const) {
    for (const frequencyHz of frequencies) {
      const pick = (exam: AudiogramRead) =>
        exam.thresholds.find(
          (row) =>
            row.ear === ear &&
            row.conduction === "air" &&
            !row.isMasked &&
            row.frequencyHz === frequencyHz,
        );
      const cur = pick(current);
      const prev = pick(previous);
      rows.push({
        ear,
        frequencyHz,
        currentLevelDb: cur?.levelDb ?? null,
        previousLevelDb: prev?.levelDb ?? null,
        currentNoResponse: cur?.isNoResponse ?? false,
        previousNoResponse: prev?.isNoResponse ?? false,
      });
    }
  }
  return rows;
}

export function latestByEar<
  T extends { ear: AudiogramEar; performedAt: string },
>(items: readonly T[]): { right: T | null; left: T | null } {
  const byEar = (ear: AudiogramEar): T | null => {
    const rows = items.filter((row) => row.ear === ear);
    if (rows.length === 0) {
      return null;
    }
    return [...rows].sort(
      (a, b) =>
        new Date(b.performedAt).getTime() - new Date(a.performedAt).getTime(),
    )[0];
  };
  return { right: byEar("right"), left: byEar("left") };
}
