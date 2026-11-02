import { describe, expect, it } from "vitest";

import { applyPlotToCells } from "../components/AudiogramChart/AudiogramGrid";
import {
  cellKey,
  frequenciesForChart,
  frequencyToX,
  levelDbToY,
  snapLevelDb,
  snapToNearestFrequency,
  thresholdsFromCells,
  thresholdsToChartPoints,
  xToFrequencyHz,
  yToLevelDb,
} from "./audiogram.utils";

describe("audiogram.utils", () => {
  it("maps descending dB HL on Y", () => {
    expect(levelDbToY(-10)).toBeLessThan(levelDbToY(130));
    expect(levelDbToY(0)).toBeLessThan(levelDbToY(60));
  });

  it("snaps level to 5 dB steps within range", () => {
    expect(snapLevelDb(42)).toBe(40);
    expect(snapLevelDb(-10)).toBe(-10);
    expect(snapLevelDb(132)).toBe(130);
  });

  it("round-trips chart coordinates on standard frequencies", () => {
    const frequencies = frequenciesForChart(false);
    const hz = snapToNearestFrequency(980, frequencies);
    expect(hz).toBe(1000);
    const x = xToFrequencyHz(frequencyToX(hz, frequencies), frequencies);
    expect(x).toBe(1000);
  });

  it("round-trips y to level", () => {
    const level = yToLevelDb(levelDbToY(55));
    expect(level).toBe(55);
  });

  it("serializes cells to threshold inputs", () => {
    const key = cellKey("right", "air", false, 1000);
    const rows = thresholdsFromCells({
      [key]: { levelDb: 25, isNoResponse: false },
    });
    expect(rows).toHaveLength(1);
    expect(rows[0]?.levelDb).toBe(25);
    const points = thresholdsToChartPoints(rows);
    expect(points[0]?.levelDb).toBe(25);
  });
});

describe("audiogram grid plot binding", () => {
  it("updates the active cell when plotting on the chart", () => {
    const mode = {
      ear: "right" as const,
      conduction: "air" as const,
      isMasked: false,
    };
    const next = applyPlotToCells({}, mode, 2000, 35);
    expect(next[cellKey("right", "air", false, 2000)]).toEqual({
      levelDb: 35,
      isNoResponse: false,
    });
  });
});
