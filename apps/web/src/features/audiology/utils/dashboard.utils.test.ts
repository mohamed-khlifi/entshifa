import { describe, expect, it } from "vitest";

import type { AudiogramRead } from "@/lib/api/generated";

import {
  buildFrequencyEvolutionSeries,
  buildThresholdComparisonRows,
  filterPointsByEar,
  latestByEar,
} from "./dashboard.utils";
import { thresholdsToChartPoints } from "./audiogram.utils";

function audiogram(
  publicId: string,
  performedAt: string,
  thresholds: AudiogramRead["thresholds"],
): AudiogramRead {
  return {
    publicId,
    performedAt,
    thresholds,
    abgLeft: null,
    abgRight: null,
    asymmetryFlag: false,
    baselineAudiogramPublicId: null,
    calibrationDate: null,
    configurationLeft: null,
    configurationRight: null,
    encounterPublicId: null,
    engineVersion: null,
    equipment: null,
    gradeLeft: null,
    gradeRight: null,
    hasExtendedHighFrequencies: false,
    interpretationText: null,
    isBaseline: false,
    isMinimumResponseLevel: false,
    isBinauralSoundfield: false,
    lossTypeLeft: null,
    lossTypeRight: null,
    method: "standard",
    patientPublicId: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    performedByPublicId: "01ARZ3NDEKTSV4RRFFQ69G5FB0",
    ptaFormula: "4freq_who",
    ptaLeft: null,
    ptaRight: null,
    reliability: "good",
    shiftFlag: false,
    status: "final",
    transducer: "headphones",
    version: 1,
  };
}

describe("dashboard.utils", () => {
  it("filters chart points by ear", () => {
    const points = thresholdsToChartPoints([
      {
        ear: "right",
        conduction: "air",
        frequencyHz: 1000,
        levelDb: 20,
        isMasked: false,
        isNoResponse: false,
      },
      {
        ear: "left",
        conduction: "air",
        frequencyHz: 1000,
        levelDb: 30,
        isMasked: false,
        isNoResponse: false,
      },
    ]);
    expect(filterPointsByEar(points, "right")).toHaveLength(1);
    expect(filterPointsByEar(points, "right")[0]?.levelDb).toBe(20);
  });

  it("builds chronological evolution samples", () => {
    const older = audiogram("a1", "2024-01-01T10:00:00Z", [
      {
        ear: "right",
        conduction: "air",
        frequencyHz: 1000,
        levelDb: 25,
        isMasked: false,
        isNoResponse: false,
      },
    ]);
    const newer = audiogram("a2", "2024-06-01T10:00:00Z", [
      {
        ear: "right",
        conduction: "air",
        frequencyHz: 1000,
        levelDb: 35,
        isMasked: false,
        isNoResponse: false,
      },
    ]);
    const series = buildFrequencyEvolutionSeries([newer, older], 1000);
    expect(series).toHaveLength(2);
    expect(series[0]?.audiogramPublicId).toBe("a1");
    expect(series[1]?.rightLevelDb).toBe(35);
  });

  it("pairs comparison rows per ear and frequency", () => {
    const current = audiogram("c", "2024-06-01T10:00:00Z", [
      {
        ear: "right",
        conduction: "air",
        frequencyHz: 500,
        levelDb: 10,
        isMasked: false,
        isNoResponse: false,
      },
    ]);
    const previous = audiogram("p", "2024-01-01T10:00:00Z", [
      {
        ear: "right",
        conduction: "air",
        frequencyHz: 500,
        levelDb: 20,
        isMasked: false,
        isNoResponse: false,
      },
    ]);
    const rows = buildThresholdComparisonRows(current, previous, [500]);
    expect(rows.find((row) => row.ear === "right")?.currentLevelDb).toBe(10);
    expect(rows.find((row) => row.ear === "right")?.previousLevelDb).toBe(20);
  });

  it("picks latest record per ear", () => {
    const picked = latestByEar([
      {
        ear: "right",
        performedAt: "2024-01-01T10:00:00Z",
        publicId: "old",
      },
      {
        ear: "right",
        performedAt: "2024-06-01T10:00:00Z",
        publicId: "new",
      },
    ]);
    expect(picked.right?.publicId).toBe("new");
  });
});
