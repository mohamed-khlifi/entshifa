"use client";

import { useTranslations } from "next-intl";
import { useCallback, useMemo } from "react";

import { CHART_HEIGHT, CHART_WIDTH } from "../../constants";
import type { OverlaySeries } from "../../types/audiology.types";
import {
  chartDbTicks,
  connectablePoints,
  frequencyAllowed,
  frequencyToX,
  levelDbToY,
  resolveSymbolDescriptor,
  thresholdsToChartPoints,
  xToFrequencyHz,
  yToLevelDb,
  type ChartPoint,
} from "../../utils/audiogram.utils";
import { formatFrequencyHz } from "../../lib/labels";
import {
  audiogramChartPointTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

import { AudiogramSymbol } from "./symbols";

type AudiogramChartProps = {
  frequencies: number[];
  points: ChartPoint[];
  overlays: OverlaySeries[];
  overlayOpacity?: number;
  readOnly: boolean;
  onPlot: (frequencyHz: number, levelDb: number) => void;
  activeEar: "right" | "left";
  activeConduction: "air" | "bone";
  activeMasked: boolean;
};

export function AudiogramChart({
  frequencies,
  points,
  overlays,
  overlayOpacity = 0.35,
  readOnly,
  onPlot,
  activeConduction,
}: AudiogramChartProps) {
  const t = useTranslations("audiology");

  const series = useMemo(
    () =>
      [
        { ear: "right", conduction: "air", isMasked: false },
        { ear: "right", conduction: "air", isMasked: true },
        { ear: "left", conduction: "air", isMasked: false },
        { ear: "left", conduction: "air", isMasked: true },
        { ear: "right", conduction: "bone", isMasked: false },
        { ear: "right", conduction: "bone", isMasked: true },
        { ear: "left", conduction: "bone", isMasked: false },
        { ear: "left", conduction: "bone", isMasked: true },
      ] as const,
    [],
  );

  const handlePointer = useCallback(
    (event: React.PointerEvent<SVGRectElement>) => {
      if (readOnly) {
        return;
      }
      const rect = event.currentTarget.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * CHART_WIDTH;
      const y = ((event.clientY - rect.top) / rect.height) * CHART_HEIGHT;
      const frequencyHz = xToFrequencyHz(x, frequencies);
      if (
        !frequencyAllowed(
          frequencyHz,
          activeConduction,
          frequencies.length > 11,
        )
      ) {
        return;
      }
      const levelDb = yToLevelDb(y);
      onPlot(frequencyHz, levelDb);
    },
    [activeConduction, frequencies, onPlot, readOnly],
  );

  return (
    <div
      dir="ltr"
      className="overflow-x-auto rounded-xl border border-border bg-card p-2"
      {...testIdProps(testIds.audiology.chart)}
    >
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        className="h-auto w-full max-w-full"
        role="img"
        aria-label={t("chart.aria")}
      >
        {chartDbTicks().map((tick) => (
          <g key={tick}>
            <line
              x1={48}
              x2={CHART_WIDTH - 24}
              y1={levelDbToY(tick)}
              y2={levelDbToY(tick)}
              stroke={tick === 0 ? "#94a3b8" : "#e2e8f0"}
              strokeWidth={tick === 0 ? 1.5 : 1}
              strokeDasharray={tick === 0 ? undefined : "4 4"}
            />
            <text
              x={8}
              y={levelDbToY(tick) + 4}
              className="fill-muted-foreground text-[10px]"
            >
              {tick}
            </text>
          </g>
        ))}
        {frequencies.map((hz) => (
          <g key={hz}>
            <line
              x1={frequencyToX(hz, frequencies)}
              x2={frequencyToX(hz, frequencies)}
              y1={24}
              y2={CHART_HEIGHT - 40}
              stroke="#e2e8f0"
              strokeWidth={1}
            />
            <text
              x={frequencyToX(hz, frequencies)}
              y={CHART_HEIGHT - 12}
              textAnchor="middle"
              className="fill-muted-foreground text-[10px]"
            >
              {formatFrequencyHz(hz)}
            </text>
          </g>
        ))}
        {overlays.flatMap((overlay) => {
          const overlayPoints = thresholdsToChartPoints(overlay.thresholds);
          return series.flatMap((row) => {
            const connected = connectablePoints(
              overlayPoints,
              row.ear,
              row.conduction,
              row.isMasked,
            );
            if (connected.length < 2) {
              return [];
            }
            const path = connected
              .map(
                (point, index) =>
                  `${index === 0 ? "M" : "L"} ${frequencyToX(point.frequencyHz, frequencies)} ${levelDbToY(point.levelDb)}`,
              )
              .join(" ");
            return (
              <path
                key={`${overlay.publicId}-${row.ear}-${row.conduction}-${row.isMasked}`}
                d={path}
                fill="none"
                stroke={row.ear === "right" ? "#dc2626" : "#2563eb"}
                strokeWidth={1}
                strokeDasharray="6 4"
                opacity={overlayOpacity}
              />
            );
          });
        })}
        {series.flatMap((row) => {
          const connected = connectablePoints(
            points,
            row.ear,
            row.conduction,
            row.isMasked,
          );
          if (connected.length < 2) {
            return [];
          }
          const path = connected
            .map(
              (point, index) =>
                `${index === 0 ? "M" : "L"} ${frequencyToX(point.frequencyHz, frequencies)} ${levelDbToY(point.levelDb)}`,
            )
            .join(" ");
          return (
            <path
              key={`${row.ear}-${row.conduction}-${row.isMasked}`}
              d={path}
              fill="none"
              stroke={row.ear === "right" ? "#dc2626" : "#2563eb"}
              strokeWidth={1.5}
            />
          );
        })}
        {points.map((point) => (
          <AudiogramSymbol
            key={`${point.ear}-${point.conduction}-${point.isMasked}-${point.frequencyHz}`}
            x={frequencyToX(point.frequencyHz, frequencies)}
            y={levelDbToY(point.levelDb)}
            descriptor={resolveSymbolDescriptor(
              point.ear,
              point.conduction,
              point.isMasked,
              point.isNoResponse,
            )}
            testId={audiogramChartPointTestId(
              point.ear,
              point.conduction,
              point.isMasked,
              point.frequencyHz,
            )}
          />
        ))}
        {!readOnly ? (
          <rect
            x={0}
            y={0}
            width={CHART_WIDTH}
            height={CHART_HEIGHT}
            fill="transparent"
            onPointerDown={handlePointer}
          />
        ) : null}
      </svg>
    </div>
  );
}
