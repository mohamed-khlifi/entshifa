"use client";

import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

export type CopiedLine = {
  id: string;
  label: string;
};

type CopyForwardPanelProps = {
  whenLabel: string;
  findingCountLabel: string;
  historyText: string | null;
  chiefComplaintSummary: string | null;
  complaints: readonly CopiedLine[];
  assessmentText: string | null;
  planText: string | null;
  problems: readonly CopiedLine[];
  problemsLoading: boolean;
  problemsError: boolean;
  confirmed: boolean;
  onConfirmAll: () => void;
};

export function CopyForwardPanel({
  whenLabel,
  findingCountLabel,
  historyText,
  chiefComplaintSummary,
  complaints,
  assessmentText,
  planText,
  problems,
  problemsLoading,
  problemsError,
  confirmed,
  onConfirmAll,
}: CopyForwardPanelProps) {
  const t = useTranslations("examination");
  return (
    <section
      data-copied={confirmed ? "false" : "true"}
      className={cn(
        "space-y-3 rounded-xl border p-4",
        confirmed ? "border-border bg-card" : "border-indigo-300 bg-indigo-50",
      )}
      {...testIdProps(testIds.examination.copyForward.banner)}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-medium">
          {t("copyForward.banner", { when: whenLabel })}
        </h2>
        {!confirmed ? (
          <span className="rounded-full border border-indigo-300 bg-card px-2.5 py-1 text-xs font-medium text-indigo-900">
            {t("copyForward.copiedBadge")}
          </span>
        ) : null}
      </div>
      <p
        className="text-sm text-muted-foreground"
        {...testIdProps(testIds.examination.copyForward.findingCount)}
      >
        {findingCountLabel}
      </p>
      <CopiedBlock
        title={t("copyForward.history")}
        testId={testIds.examination.copyForward.history}
      >
        {historyText ? historyText : t("copyForward.historyEmpty")}
      </CopiedBlock>
      {chiefComplaintSummary ? (
        <CopiedBlock title={t("copyForward.complaint")}>
          {chiefComplaintSummary}
        </CopiedBlock>
      ) : null}
      <div {...testIdProps(testIds.examination.copyForward.complaints)}>
        <h3 className="text-sm font-medium">{t("copyForward.complaints")}</h3>
        {complaints.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("copyForward.complaintsEmpty")}
          </p>
        ) : (
          <ul className="list-disc space-y-1 ps-5">
            {complaints.map((row) => (
              <li key={row.id} className="text-sm leading-6">
                {row.label}
              </li>
            ))}
          </ul>
        )}
      </div>
      {assessmentText ? (
        <CopiedBlock title={t("copyForward.assessment")}>
          {assessmentText}
        </CopiedBlock>
      ) : null}
      {planText ? (
        <CopiedBlock title={t("copyForward.plan")}>{planText}</CopiedBlock>
      ) : null}
      <div {...testIdProps(testIds.examination.copyForward.problems)}>
        <h3 className="text-sm font-medium">{t("copyForward.problems")}</h3>
        {problemsLoading ? (
          <p className="text-sm text-muted-foreground">
            {t("copyForward.problemsLoading")}
          </p>
        ) : null}
        {problemsError ? (
          <p className="text-sm text-destructive">
            {t("copyForward.problemsError")}
          </p>
        ) : null}
        {!problemsLoading && !problemsError && problems.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("copyForward.problemsEmpty")}
          </p>
        ) : null}
        {!problemsLoading && !problemsError && problems.length > 0 ? (
          <ul className="list-disc space-y-1 ps-5">
            {problems.map((row) => (
              <li key={row.id} className="text-sm leading-6">
                {row.label}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
      {!confirmed ? (
        <Button
          type="button"
          onClick={onConfirmAll}
          {...testIdProps(testIds.examination.copyForward.confirmAll)}
        >
          {t("copyForward.confirmAll")}
        </Button>
      ) : null}
    </section>
  );
}

function CopiedBlock({
  title,
  children,
  testId,
}: {
  title: string;
  children: string;
  testId?: string;
}) {
  return (
    <div {...(testId ? testIdProps(testId) : {})}>
      <h3 className="text-sm font-medium">{title}</h3>
      <p className="text-sm leading-6">{children}</p>
    </div>
  );
}
