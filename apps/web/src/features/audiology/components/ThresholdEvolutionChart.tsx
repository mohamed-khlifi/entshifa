"use client";

import { useTranslations } from "next-intl";
import { useMemo } from "react";

import {
  CHART_HEIGHT,
  CHART_PADDING,
  CHART_WIDTH,
  MIN_LEVEL_DB,
  MAX_LEVEL_DB,
} from "../constants";
import { earColor } from "../utils/audiogram.utils";
import type { EvolutionSample } from "../utils/dashboard.utils";
import { formatDate } from "@/lib/i18n/format";
import { testIdProps, testIds } from "@/lib/test/test-id";

type ThresholdEvolutionChartProps = {
  samples: EvolutionSample[];
  locale: string;
};

function timeToX(
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

function levelToY(
  levelDb: number,
  innerHeight: number,
  paddingTop: number,
): number {
  const ratio = (levelDb - MIN_LEVEL_DB) / (MAX_LEVEL_DB - MIN_LEVEL_DB);
  return paddingTop + ratio * innerHeight;
}

export function ThresholdEvolutionChart({
  samples,
  locale,
}: ThresholdEvolutionChartProps) {
  const t = useTranslations("audiology");
  const innerWidth = CHART_WIDTH - CHART_PADDING.left - CHART_PADDING.right;
  const innerHeight = CHART_HEIGHT - CHART_PADDING.top - CHART_PADDING.bottom;

  const points = useMemo(() => {
    return samples.map((sample, index) => ({
      sample,
      index,
      x: timeToX(index, samples.length, innerWidth, CHART_PADDING.left),
    }));
  }, [innerWidth, samples]);

  const series = useMemo(
    () =>
      [
        {
          ear: "right" as const,
          key: "rightLevelDb" as const,
          nr: "rightNoResponse" as const,
        },
        {
          ear: "left" as const,
          key: "leftLevelDb" as const,
          nr: "leftNoResponse" as const,
        },
      ] as const,
    [],
  );

  return (
    <section
      className="space-y-2"
      dir="ltr"
      {...testIdProps(testIds.audiology.evolutionChart)}
    >
      <h3 className="text-sm font-semibold">{t("dashboard.evolutionTitle")}</h3>
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        className="h-48 w-full max-w-3xl rounded-lg border border-border bg-card"
        role="img"
        aria-label={t("dashboard.evolutionAria")}
      >
        {[0, 25, 50, 75, 100].map((tick) => {
          const y = CHART_PADDING.top + (tick / 100) * innerHeight;
          const db =
            MIN_LEVEL_DB + (tick / 100) * (MAX_LEVEL_DB - MIN_LEVEL_DB);
          return (
            <g key={tick}>
              <line
                x1={CHART_PADDING.left}
                x2={CHART_WIDTH - CHART_PADDING.right}
                y1={y}
                y2={y}
                className="stroke-border"
                strokeWidth={0.5}
              />
              <text
                x={CHART_PADDING.left - 6}
                y={y + 4}
                textAnchor="end"
                className="fill-muted-foreground text-[10px]"
              >
                {db}
              </text>
            </g>
          );
        })}
        {points.map(({ sample, x }) => (
          <text
            key={sample.audiogramPublicId}
            x={x}
            y={CHART_HEIGHT - 4}
            textAnchor="middle"
            className="fill-muted-foreground text-[9px]"
          >
            {formatDate(sample.performedAt, locale, { dateStyle: "short" })}
          </text>
        ))}
        {series.map(({ ear, key, nr }) => {
          const plotted = points.filter(
            ({ sample }) => sample[key] !== null && !sample[nr],
          );
          if (plotted.length < 2) {
            return null;
          }
          const path = plotted
            .map(({ sample, x }, idx) => {
              const y = levelToY(
                sample[key] as number,
                innerHeight,
                CHART_PADDING.top,
              );
              return `${idx === 0 ? "M" : "L"} ${x} ${y}`;
            })
            .join(" ");
          return (
            <path
              key={ear}
              d={path}
              fill="none"
              stroke={earColor(ear)}
              strokeWidth={2}
            />
          );
        })}
        {series.flatMap(({ ear, key, nr }) =>
          points
            .filter(({ sample }) => sample[key] !== null)
            .map(({ sample, x }) => {
              const level = sample[key] as number;
              const y = levelToY(level, innerHeight, CHART_PADDING.top);
              return (
                <circle
                  key={`${ear}-${sample.audiogramPublicId}`}
                  cx={x}
                  cy={y}
                  r={sample[nr] ? 5 : 4}
                  fill={sample[nr] ? "none" : earColor(ear)}
                  stroke={earColor(ear)}
                  strokeWidth={sample[nr] ? 2 : 0}
                />
              );
            }),
        )}
      </svg>
    </section>
  );
}
