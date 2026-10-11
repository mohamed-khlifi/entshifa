"use client";

import { useLocale, useTranslations } from "next-intl";

import {
  compareStructures,
  scoreTrend,
  type EndoscopyDraft,
} from "../lib/draft";
import {
  comparisonChangeLabel,
  lateralityLabel,
  polypScaleLabel,
  structureStatusLabel,
} from "../lib/labels";
import { examinationRegionLabel } from "@/lib/anatomy/region-labels";
import { nasalEndoscopyMap } from "@/lib/anatomy";
import type { EndoscopyExamRead, ResolvedConcept } from "@/lib/api/generated";
import { formatDate, formatNumber } from "@/lib/i18n/format";
import {
  endoscopyComparisonTestId,
  endoscopyTrendTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

type EndoscopyComparisonProps = {
  draft: EndoscopyDraft;
  previous: EndoscopyExamRead | null;
  exams: readonly EndoscopyExamRead[];
  findings: readonly ResolvedConcept[];
};

export function EndoscopyComparison({
  draft,
  previous,
  exams,
  findings,
}: EndoscopyComparisonProps) {
  const t = useTranslations("endoscopy");
  const tExam = useTranslations("examination");
  const locale = useLocale();
  if (!previous) {
    return (
      <p
        className="text-sm text-muted-foreground"
        {...testIdProps(testIds.endoscopy.comparisonEmpty)}
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
      {...testIdProps(testIds.endoscopy.comparison)}
    >
      <h3 className="text-sm font-semibold">{t("comparison.title")}</h3>
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
              const region = nasalEndoscopyMap.regions.find(
                (item) => item.bodySiteCode === row.bodySiteCode,
              );
              const currentFinding = findings.find(
                (finding) => finding.code === row.currentFindingCode,
              );
              return (
                <tr
                  key={`${row.laterality}:${row.bodySiteCode}`}
                  data-change={row.change}
                  className={
                    row.change === "changed" ? "bg-amber-500/15" : undefined
                  }
                  {...testIdProps(
                    endoscopyComparisonTestId(row.bodySiteCode, row.laterality),
                  )}
                >
                  <td className="px-2 py-1">
                    {region
                      ? examinationRegionLabel(tExam, region.labelKey)
                      : t("comparison.structure")}
                    <span className="ms-2 text-xs text-muted-foreground">
                      {lateralityLabel(t, row.laterality)}
                    </span>
                  </td>
                  <td className="px-2 py-1">
                    {row.previousDisplay ??
                      structureStatusLabel(t, row.previousStatus)}
                  </td>
                  <td className="px-2 py-1">
                    {currentFinding?.display ??
                      structureStatusLabel(t, row.currentStatus)}
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
      <div {...testIdProps(testIds.endoscopy.trend)}>
        <h4 className="text-sm font-semibold">{t("comparison.trend")}</h4>
        <ol className="mt-2 space-y-1 text-sm">
          {trend.map((point) => (
            <li
              key={point.examId}
              data-changed={point.lundKennedyChanged ? "true" : "false"}
              {...testIdProps(endoscopyTrendTestId(point.examId))}
            >
              {formatDate(point.performedAt, locale, {
                year: "numeric",
                month: "short",
                day: "numeric",
              })}
              <span className="ms-2">{t("scores.lundKennedy")}</span>
              <span className="ms-2">
                {formatNumber(point.lundKennedyTotal, locale)}
              </span>
              <span className="ms-2">{t("scores.modified")}</span>
              <span className="ms-2">
                {formatNumber(point.modifiedLkTotal, locale)}
              </span>
              <span className="ms-2">
                {polypScaleLabel(t, point.polypScale)}
              </span>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
