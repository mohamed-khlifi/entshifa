"use client";

import { useLocale, useTranslations } from "next-intl";

import { Card } from "@/components/ui/card";
import type { QuestionnaireResponseRead } from "@/lib/api/generated";
import { formatDate, formatNumber } from "@/lib/i18n/format";
import { testIdProps, testIds } from "@/lib/test/test-id";

import { severityBandLabel, subscaleLabel } from "../lib/labels";

type QuestionnaireScoreSummaryCardProps = {
  response: QuestionnaireResponseRead;
};

export function QuestionnaireScoreSummaryCard({
  response,
}: QuestionnaireScoreSummaryCardProps) {
  const t = useTranslations("questionnaires");
  const locale = useLocale();
  const band = severityBandLabel(t, response.severityBand);
  const delta =
    response.changeFromPrevious !== null &&
    response.changeFromPrevious !== undefined
      ? Number(response.changeFromPrevious)
      : null;
  const mcid =
    response.mcid !== null && response.mcid !== undefined
      ? Number(response.mcid)
      : null;

  return (
    <Card
      className="space-y-4 p-4"
      {...testIdProps(testIds.questionnaires.scoreCard)}
    >
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-lg font-semibold">
            {response.instrumentTitle ?? response.instrumentCode}
          </h3>
          <p className="text-sm text-muted-foreground">
            {t("presentation.completedOn", {
              date: formatDate(response.completedAt, locale, {
                dateStyle: "medium",
              }),
            })}
          </p>
        </div>
        <span
          className="rounded bg-muted px-2 py-0.5 text-xs"
          {...testIdProps(testIds.questionnaires.provenanceBadge)}
        >
          {response.enteredBy === "patient"
            ? t("delivery.provenancePatient")
            : response.enteredBy === "clinician"
              ? t("delivery.provenanceClinician")
              : t("delivery.provenanceStaff")}
        </span>
      </header>
      <div className="flex flex-wrap items-baseline gap-3">
        <p
          className="text-3xl font-semibold tabular-nums"
          {...testIdProps(testIds.questionnaires.totalScore)}
        >
          {formatNumber(Number(response.totalScore), locale)}
        </p>
        <p className="text-sm text-muted-foreground">
          {t("presentation.scoreRange", {
            min: response.minScore,
            max: response.maxScore,
          })}
        </p>
        {band ? (
          <span
            className="rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary"
            {...testIdProps(testIds.questionnaires.severityBand)}
          >
            {band}
          </span>
        ) : null}
      </div>
      {Object.keys(response.subscaleScores).length > 0 ? (
        <section {...testIdProps(testIds.questionnaires.subscaleList)}>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t("presentation.subscalesTitle")}
          </h4>
          <ul className="mt-2 grid gap-2 sm:grid-cols-2">
            {Object.entries(response.subscaleScores).map(([code, value]) => (
              <li
                key={code}
                className="flex justify-between rounded-md border px-3 py-2 text-sm"
              >
                <span>{subscaleLabel(t, code)}</span>
                <span className="font-medium tabular-nums">
                  {formatNumber(Number(value), locale)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <section className="space-y-1 text-sm">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {t("presentation.changeTitle")}
        </h4>
        {delta === null ? (
          <p className="text-muted-foreground">
            {t("presentation.noPrevious")}
          </p>
        ) : (
          <div className="flex flex-wrap items-center gap-2">
            <span
              className="font-medium tabular-nums"
              {...testIdProps(testIds.questionnaires.changeFromPrevious)}
            >
              {t("presentation.changeValue", { delta })}
            </span>
            {mcid !== null ? (
              <span
                className="text-muted-foreground"
                {...testIdProps(testIds.questionnaires.mcidBadge)}
              >
                {t("presentation.mcidLabel", {
                  mcid: formatNumber(mcid, locale),
                })}
                {" · "}
                {response.mcidReached
                  ? t("presentation.mcidReached")
                  : t("presentation.mcidNotReached")}
              </span>
            ) : null}
          </div>
        )}
      </section>
    </Card>
  );
}
