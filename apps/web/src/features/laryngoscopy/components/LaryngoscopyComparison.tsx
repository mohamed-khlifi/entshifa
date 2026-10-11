"use client";

import { useLocale, useTranslations } from "next-intl";

import {
  compareStructures,
  scoreTrend,
  type LaryngoscopyDraft,
} from "../lib/draft";
import {
  comparisonChangeLabel,
  lateralityLabel,
  mobilityLabel,
  structureStatusLabel,
} from "../lib/labels";
import { examinationRegionLabel } from "@/lib/anatomy/region-labels";
import { larynxMap } from "@/lib/anatomy";
import type { LaryngoscopyExamRead } from "@/lib/api/generated";
import { formatDate, formatNumber } from "@/lib/i18n/format";
import {
  laryngoscopyComparisonTestId,
  laryngoscopyTrendTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

type LaryngoscopyComparisonProps = {
  draft: LaryngoscopyDraft;
  previous: LaryngoscopyExamRead | null;
  exams: readonly LaryngoscopyExamRead[];
};

export function LaryngoscopyComparison({
  draft,
  previous,
  exams,
}: LaryngoscopyComparisonProps) {
  const t = useTranslations("laryngoscopy");
  const tExam = useTranslations("examination");
  const locale = useLocale();
  if (!previous) {
    return (
      <p
        className="text-sm text-muted-foreground"
        {...testIdProps(testIds.laryngoscopy.comparisonEmpty)}
      >
        {t("comparison.empty")}
      </p>
    );
  }
  const rows = compareStructures(draft.structures, previous.structures);
  const trend = scoreTrend(exams);
  return (
    <section
      className="space-y-4"
      {...testIdProps(testIds.laryngoscopy.comparison)}
    >
      <h3 className="text-sm font-semibold">{t("comparison.title")}</h3>
      <p className="text-sm">
        {t("comparison.mobility")}:{" "}
        {mobilityLabel(t, previous.vocalFoldRight.mobility)} /{" "}
        {mobilityLabel(t, previous.vocalFoldLeft.mobility)}
      </p>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[36rem] text-sm">
          <thead>
            <tr className="text-start text-xs text-muted-foreground">
              <th className="px-2 py-1 text-start">
                {t("comparison.structure")}
              </th>
              <th className="px-2 py-1 text-start">
                {t("comparison.previous")}
              </th>
              <th className="px-2 py-1 text-start">
                {t("comparison.current")}
              </th>
              <th className="px-2 py-1 text-start">
                {t("comparison.changed")}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const region = larynxMap.regions.find(
                (item) => item.bodySiteCode === row.bodySiteCode,
              );
              const label = region
                ? examinationRegionLabel(tExam, region.labelKey)
                : row.bodySiteCode;
              return (
                <tr
                  key={`${row.bodySiteCode}:${row.laterality}`}
                  className={
                    row.change === "changed" ? "bg-amber-500/15" : undefined
                  }
                  data-change={row.change}
                  {...testIdProps(
                    laryngoscopyComparisonTestId(
                      row.bodySiteCode,
                      row.laterality,
                    ),
                  )}
                >
                  <td className="px-2 py-1">
                    {label} {lateralityLabel(t, row.laterality)}
                  </td>
                  <td className="px-2 py-1">
                    {row.previousDisplay ??
                      structureStatusLabel(t, row.previousStatus)}
                  </td>
                  <td className="px-2 py-1">
                    {structureStatusLabel(t, row.currentStatus)}
                  </td>
                  <td className="px-2 py-1">
                    {comparisonChangeLabel(t, row.change)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div {...testIdProps(testIds.laryngoscopy.trend)}>
        <h4 className="text-sm font-semibold">{t("comparison.trend")}</h4>
        <ul className="mt-2 space-y-1 text-sm">
          {trend.map((point) => (
            <li
              key={point.examId}
              {...testIdProps(laryngoscopyTrendTestId(point.examId))}
            >
              {formatDate(point.performedAt, locale)}
              {" · "}
              {t("scores.rfs")} {formatNumber(point.rfsScore ?? 0, locale)}
              {" · "}
              {t("scores.grbas")} {formatNumber(point.grbasTotal ?? 0, locale)}
              {" · "}
              {t("scores.pas")} {formatNumber(point.pasScore ?? 0, locale)}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
