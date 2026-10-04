"use client";

import { useTranslations } from "next-intl";

import { testIdProps, testIds } from "@/lib/test/test-id";

type ReportPreviewProps = {
  complaints: string;
  history: string;
  examination: string;
  flags: string;
  assessment: string;
  plan: string;
};

export function ReportPreview({
  complaints,
  history,
  examination,
  flags,
  assessment,
  plan,
}: ReportPreviewProps) {
  const t = useTranslations("encounters");
  const empty =
    complaints.length === 0 &&
    history.length === 0 &&
    examination.length === 0 &&
    flags.length === 0 &&
    assessment.length === 0 &&
    plan.length === 0;

  return (
    <aside
      className="space-y-4 rounded-xl border border-border bg-card p-4 shadow-[var(--shadow-soft)]"
      {...testIdProps(testIds.encounters.preview)}
    >
      <h2 className="text-lg font-semibold">{t("preview.title")}</h2>
      {empty ? (
        <p className="text-sm text-muted-foreground">{t("preview.empty")}</p>
      ) : null}
      <PreviewBlock title={t("preview.complaints")} body={complaints} />
      <PreviewBlock title={t("preview.history")} body={history} />
      <PreviewBlock
        title={t("preview.examination")}
        body={examination}
        emptyLabel={t("preview.examinationEmpty")}
      />
      <PreviewBlock title={t("preview.flags")} body={flags} />
      <PreviewBlock title={t("preview.assessment")} body={assessment} />
      <PreviewBlock title={t("preview.plan")} body={plan} />
    </aside>
  );
}

function PreviewBlock({
  title,
  body,
  emptyLabel,
}: {
  title: string;
  body: string;
  emptyLabel?: string;
}) {
  if (body.length === 0 && !emptyLabel) {
    return null;
  }
  return (
    <section className="space-y-1">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h3>
      <p className="whitespace-pre-wrap text-sm">
        {body.length > 0 ? body : emptyLabel}
      </p>
    </section>
  );
}
