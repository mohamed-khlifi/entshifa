import type { QuestionnaireResponseRead } from "@/lib/api/generated";

export type TrendPoint = {
  publicId: string;
  completedAt: string;
  totalScore: number;
  minScore: number;
  maxScore: number;
};

export type TreatmentMarker = {
  publicId: string;
  occurredAt: string;
  eventType: string;
};

export const CHART_WIDTH = 640;
export const CHART_HEIGHT = 200;
export const CHART_PADDING = { left: 48, right: 24, top: 16, bottom: 40 };

export function toTrendPoints(
  rows: readonly QuestionnaireResponseRead[],
): TrendPoint[] {
  return [...rows]
    .map((row) => ({
      publicId: row.publicId,
      completedAt: row.completedAt,
      totalScore: Number(row.totalScore),
      minScore: row.minScore,
      maxScore: row.maxScore,
    }))
    .sort(
      (a, b) =>
        new Date(a.completedAt).getTime() - new Date(b.completedAt).getTime(),
    );
}

export function timeToX(
  index: number,
  count: number,
  innerWidth: number,
  paddingLeft: number,
): number {
  if (count <= 1) {
    return paddingLeft + innerWidth / 2;
  }
  return paddingLeft + (index / (count - 1)) * innerWidth;
}

export function scoreToY(
  score: number,
  minScore: number,
  maxScore: number,
  innerHeight: number,
  paddingTop: number,
): number {
  const span = Math.max(maxScore - minScore, 1);
  const ratio = (score - minScore) / span;
  return paddingTop + (1 - ratio) * innerHeight;
}

export function markerXForDate(
  occurredAt: string,
  points: TrendPoint[],
  innerWidth: number,
  paddingLeft: number,
): number | null {
  if (points.length === 0) {
    return null;
  }
  const target = new Date(occurredAt).getTime();
  const times = points.map((p) => new Date(p.completedAt).getTime());
  const minT = times[0] ?? target;
  const maxT = times[times.length - 1] ?? target;
  if (maxT <= minT) {
    return paddingLeft + innerWidth / 2;
  }
  const ratio = Math.min(1, Math.max(0, (target - minT) / (maxT - minT)));
  return paddingLeft + ratio * innerWidth;
}
