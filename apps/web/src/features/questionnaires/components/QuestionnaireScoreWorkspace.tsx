"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";

import { usePatientTimelineInfinite } from "@/features/patients";
import {
  usePatientQuestionnaireResponses,
  useQuestionnaireResponseDetail,
} from "../hooks/use-questionnaire-queries";
import { toTrendPoints } from "../utils/trend.utils";
import { QuestionnaireItemBreakdown } from "./QuestionnaireItemBreakdown";
import { QuestionnaireScoreSummaryCard } from "./QuestionnaireScoreSummaryCard";
import { QuestionnaireTrendChart } from "./QuestionnaireTrendChart";

type QuestionnaireScoreWorkspaceProps = {
  patientId: string;
  instrumentCode: string;
};

export function QuestionnaireScoreWorkspace({
  patientId,
  instrumentCode,
}: QuestionnaireScoreWorkspaceProps) {
  const t = useTranslations("questionnaires");
  const locale = useLocale();
  const responses = usePatientQuestionnaireResponses(patientId, {
    instrumentCode,
  });
  const timeline = usePatientTimelineInfinite(patientId, {});
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const items = useMemo(
    () => responses.data?.items ?? [],
    [responses.data?.items],
  );

  useEffect(() => {
    if (items.length === 0) {
      setSelectedId(null);
      return;
    }
    if (selectedId && items.some((row) => row.publicId === selectedId)) {
      return;
    }
    setSelectedId(items[0]?.publicId ?? null);
  }, [items, selectedId]);

  const selected =
    items.find((row) => row.publicId === selectedId) ?? items[0] ?? null;
  const detail = useQuestionnaireResponseDetail(
    selected?.publicId ?? null,
    locale,
  );
  const points = useMemo(
    () =>
      toTrendPoints(
        items.filter((row) => row.instrumentCode === instrumentCode),
      ),
    [instrumentCode, items],
  );
  const events = useMemo(
    () => timeline.data?.pages.flatMap((page) => page.items) ?? [],
    [timeline.data],
  );

  if (responses.isLoading) {
    return (
      <p className="text-sm text-muted-foreground">{t("delivery.loading")}</p>
    );
  }

  if (items.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        {t("delivery.emptyHistory")}
      </p>
    );
  }

  return (
    <div className="space-y-6">
      {selected ? <QuestionnaireScoreSummaryCard response={selected} /> : null}
      <QuestionnaireTrendChart
        points={points}
        events={events}
        selectedId={selected?.publicId ?? null}
        onSelect={setSelectedId}
      />
      {detail.isLoading ? (
        <p className="text-sm text-muted-foreground">
          {t("presentation.loadingDetail")}
        </p>
      ) : null}
      {detail.isError ? (
        <p className="text-sm text-destructive">
          {t("presentation.errorDetail")}
        </p>
      ) : null}
      {detail.data?.items ? (
        <QuestionnaireItemBreakdown items={detail.data.items} />
      ) : null}
    </div>
  );
}
