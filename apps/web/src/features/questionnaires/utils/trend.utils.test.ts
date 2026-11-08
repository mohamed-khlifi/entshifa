import { describe, expect, it } from "vitest";

import type { QuestionnaireResponseRead } from "@/lib/api/generated";

import {
  markerXForDate,
  scoreToY,
  timeToX,
  toTrendPoints,
} from "./trend.utils";

function response(
  publicId: string,
  completedAt: string,
  totalScore: string,
): QuestionnaireResponseRead {
  return {
    publicId,
    completedAt,
    totalScore,
    minScore: 0,
    maxScore: 110,
    instrumentCode: "snot22",
    instrumentTitle: "SNOT-22",
    locale: "en",
    enteredBy: "patient",
    encounterId: null,
    severityBand: "moderate",
    subscaleScores: {},
    changeFromPrevious: null,
    mcid: "8.9",
    mcidReached: null,
  };
}

describe("trend.utils", () => {
  it("sorts trend points chronologically", () => {
    const points = toTrendPoints([
      response("b", "2025-06-02T10:00:00Z", "40"),
      response("a", "2025-06-01T10:00:00Z", "30"),
    ]);
    expect(points.map((p) => p.publicId)).toEqual(["a", "b"]);
    expect(points[0]?.totalScore).toBe(30);
  });

  it("maps score to chart Y with inverted axis", () => {
    const inner = 120;
    const top = 16;
    expect(scoreToY(0, 0, 100, inner, top)).toBe(top + inner);
    expect(scoreToY(100, 0, 100, inner, top)).toBe(top);
    expect(scoreToY(50, 0, 100, inner, top)).toBe(top + inner / 2);
  });

  it("distributes X positions across indices", () => {
    expect(timeToX(0, 3, 400, 48)).toBe(48);
    expect(timeToX(2, 3, 400, 48)).toBe(448);
    expect(timeToX(0, 1, 400, 48)).toBe(248);
  });

  it("interpolates treatment markers between first and last score dates", () => {
    const points = toTrendPoints([
      response("a", "2025-01-01T00:00:00Z", "10"),
      response("b", "2025-01-03T00:00:00Z", "20"),
    ]);
    const mid = markerXForDate("2025-01-02T12:00:00Z", points, 544, 48);
    expect(mid).not.toBeNull();
    expect(mid!).toBeGreaterThan(48);
    expect(mid!).toBeLessThan(592);
  });
});
