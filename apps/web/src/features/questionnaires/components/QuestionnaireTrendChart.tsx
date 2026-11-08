"use client";

import { useLocale, useTranslations } from "next-intl";
import { useMemo } from "react";

import type { PatientTimelineItemRead } from "@/lib/api/generated";
import { formatDate, formatNumber } from "@/lib/i18n/format";
import {
  questionnaireTrendPointTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

import { isTreatmentTimelineEvent, treatmentEventLabel } from "../lib/labels";
import {
  CHART_HEIGHT,
  CHART_PADDING,
  CHART_WIDTH,
  markerXForDate,
  scoreToY,
  timeToX,
  type TrendPoint,
  type TreatmentMarker,
} from "../utils/trend.utils";

type QuestionnaireTrendChartProps = {
  points: TrendPoint[];
  events: readonly PatientTimelineItemRead[];
  selectedId: string | null;
  onSelect: (publicId: string) => void;
};

export function QuestionnaireTrendChart({
  points,
  events,
  selectedId,
  onSelect,
}: QuestionnaireTrendChartProps) {
  const t = useTranslations("questionnaires");
  const locale = useLocale();
  const innerWidth = CHART_WIDTH - CHART_PADDING.left - CHART_PADDING.right;
  const innerHeight = CHART_HEIGHT - CHART_PADDING.top - CHART_PADDING.bottom;

  const markers: TreatmentMarker[] = useMemo(
    () =>
      events
        .filter((row) => isTreatmentTimelineEvent(row.eventType))
        .map((row) => ({
          publicId: row.publicId,
          occurredAt: row.occurredAt,
          eventType: row.eventType,
        })),
    [events],
  );

  const scale = points[0] ?? { minScore: 0, maxScore: 100 };

  if (points.length === 0) {
    return (
      <p
        className="text-sm text-muted-foreground"
        {...testIdProps(testIds.questionnaires.trendEmpty)}
      >
        {t("presentation.trendEmpty")}
      </p>
    );
  }

  const plotted = points.map((point, index) => ({
    point,
    index,
    x: timeToX(index, points.length, innerWidth, CHART_PADDING.left),
    y: scoreToY(
      point.totalScore,
      point.minScore,
      point.maxScore,
      innerHeight,
      CHART_PADDING.top,
    ),
  }));

  const path =
    plotted.length >= 2
      ? plotted
          .map((row, idx) => `${idx === 0 ? "M" : "L"} ${row.x} ${row.y}`)
          .join(" ")
      : null;

  const yTicks = [scale.minScore, scale.maxScore] as const;

  return (
    <section
      className="space-y-2"
      dir="ltr"
      {...testIdProps(testIds.questionnaires.trendChart)}
    >
      <h3 className="text-sm font-semibold">{t("presentation.trendTitle")}</h3>
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        className="h-48 w-full max-w-3xl rounded-lg border border-border bg-card"
        role="img"
        aria-label={t("presentation.trendAria")}
      >
        {yTicks.map((tick) => {
          const y = scoreToY(
            tick,
            scale.minScore,
            scale.maxScore,
            innerHeight,
            CHART_PADDING.top,
          );
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
                {formatNumber(tick, locale)}
              </text>
            </g>
          );
        })}
        {markers.map((marker) => {
          const x = markerXForDate(
            marker.occurredAt,
            points,
            innerWidth,
            CHART_PADDING.left,
          );
          if (x === null) {
            return null;
          }
          return (
            <line
              key={marker.publicId}
              x1={x}
              x2={x}
              y1={CHART_PADDING.top}
              y2={CHART_HEIGHT - CHART_PADDING.bottom}
              className="stroke-amber-500"
              strokeWidth={1}
              strokeDasharray="4 3"
              {...testIdProps(testIds.questionnaires.trendEventMarker)}
            />
          );
        })}
        {path ? (
          <path
            d={path}
            fill="none"
            className="stroke-primary"
            strokeWidth={2}
          />
        ) : null}
        {plotted.map(({ point, x, y }) => (
          <g key={point.publicId}>
            <circle
              cx={x}
              cy={y}
              r={selectedId === point.publicId ? 6 : 5}
              className={cn(
                "cursor-pointer",
                selectedId === point.publicId
                  ? "fill-primary"
                  : "fill-card stroke-primary",
              )}
              strokeWidth={2}
              onClick={() => onSelect(point.publicId)}
              {...testIdProps(questionnaireTrendPointTestId(point.publicId))}
            />
          </g>
        ))}
        {plotted.map(({ point, x }) => (
          <text
            key={`${point.publicId}-label`}
            x={x}
            y={CHART_HEIGHT - 6}
            textAnchor="middle"
            className="fill-muted-foreground text-[9px]"
          >
            {formatDate(point.completedAt, locale, { dateStyle: "short" })}
          </text>
        ))}
      </svg>
      {markers.length > 0 ? (
        <p className="text-xs text-muted-foreground">
          {t("presentation.eventsLegend")}:{" "}
          {markers
            .map((m) => treatmentEventLabel(t, m.eventType))
            .filter(Boolean)
            .join(" · ")}
        </p>
      ) : null}
    </section>
  );
}
