"use client";

import { useLocale, useTranslations } from "next-intl";
import { useCallback, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { ApiError, resolveErrorMessage } from "@/lib/api/errors";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

import {
  usePublicQuestionnaireSession,
  useSubmitPublicQuestionnaire,
} from "../hooks/use-questionnaire-queries";
import type { PublicInstrumentItem } from "../types";

type PublicQuestionnaireRunnerProps = {
  token: string;
};

export function PublicQuestionnaireRunner({
  token,
}: PublicQuestionnaireRunnerProps) {
  const t = useTranslations("questionnaires");
  const tErrors = useTranslations("errors");
  const locale = useLocale();
  const session = usePublicQuestionnaireSession(token);
  const submit = useSubmitPublicQuestionnaire(token);
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [done, setDone] = useState(false);

  const items: PublicInstrumentItem[] = useMemo(
    () =>
      session.data
        ? [...session.data.instrument.items].sort(
            (a, b) => a.position - b.position,
          )
        : [],
    [session.data],
  );

  const current = items[step] ?? null;

  const onSelect = useCallback(
    (value: number) => {
      if (!current) {
        return;
      }
      setAnswers((prev) => ({ ...prev, [current.code]: value }));
    },
    [current],
  );

  if (session.isLoading) {
    return (
      <p
        className="text-muted-foreground"
        {...testIdProps(testIds.questionnaires.runner)}
      >
        {t("runner.loading")}
      </p>
    );
  }

  if (session.isError) {
    const apiErr =
      session.error instanceof ApiError
        ? session.error
        : new ApiError({ code: "internal_error", status: 500, context: {} });
    const code = apiErr.code;
    if (code === "questionnaire.invitation_expired") {
      return (
        <StateCard
          title={t("runner.expiredTitle")}
          body={t("runner.expiredBody")}
        />
      );
    }
    if (code === "questionnaire.invitation_already_completed") {
      return (
        <StateCard
          title={t("runner.completedTitle")}
          body={t("runner.completedBody")}
        />
      );
    }
    if (code === "questionnaire.rate_limited") {
      return (
        <StateCard
          title={t("runner.rateLimitedTitle")}
          body={t("runner.rateLimitedBody")}
        />
      );
    }
    if (code === "questionnaire.invitation_not_found") {
      return (
        <StateCard
          title={t("runner.notFoundTitle")}
          body={t("runner.notFoundBody")}
        />
      );
    }
    return (
      <p className="text-destructive">
        {resolveErrorMessage(apiErr, tErrors as (key: string) => string)}
      </p>
    );
  }

  if (!session.data) {
    return null;
  }

  if (done) {
    return (
      <div
        className="mx-auto max-w-lg space-y-4 text-center"
        {...testIdProps(testIds.questionnaires.runnerComplete)}
      >
        <h1 className="text-2xl font-semibold">{t("runner.completeTitle")}</h1>
        <p>{t("runner.completeBody")}</p>
        {session.data.channel === "tablet" ? (
          <p className="text-sm text-muted-foreground">
            {t("runner.tabletHandback")}
          </p>
        ) : null}
      </div>
    );
  }

  const handleSubmit = async () => {
    await submit.mutateAsync(answers);
    setDone(true);
  };

  return (
    <div
      className="mx-auto flex min-h-[70vh] max-w-lg flex-col gap-6 px-4 py-8"
      {...testIdProps(testIds.questionnaires.runner)}
      lang={locale}
    >
      <header className="space-y-1 text-center">
        <p className="text-sm text-muted-foreground">
          {session.data.clinicName}
        </p>
        <h1 className="text-xl font-semibold">
          {t("runner.greeting", { firstName: session.data.patientFirstName })}
        </h1>
        <p className="text-lg">{session.data.instrument.title}</p>
      </header>
      <div
        className="text-center text-sm text-muted-foreground"
        {...testIdProps(testIds.questionnaires.runnerProgress)}
      >
        {t("runner.progress", { current: step + 1, total: items.length })}
      </div>
      {current ? (
        <div
          className="flex flex-1 flex-col gap-4"
          {...testIdProps(testIds.questionnaires.runnerQuestion)}
        >
          <p className="text-lg font-medium leading-snug">{current.text}</p>
          <div className="flex flex-col gap-2">
            {current.options
              .slice()
              .sort((a, b) => a.position - b.position)
              .map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  className={cn(
                    "min-h-14 rounded-lg border px-4 py-3 text-start text-base transition",
                    answers[current.code] === opt.value
                      ? "border-primary bg-primary/10"
                      : "border-border bg-card hover:bg-muted/60",
                  )}
                  onClick={() => onSelect(opt.value)}
                  {...testIdProps(testIds.questionnaires.runnerOption)}
                >
                  {opt.text}
                </button>
              ))}
          </div>
        </div>
      ) : null}
      <div className="flex gap-2">
        <Button
          type="button"
          variant="secondary"
          className="flex-1"
          disabled={step === 0}
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          {...testIdProps(testIds.questionnaires.runnerPrevious)}
        >
          {t("runner.previous")}
        </Button>
        {step < items.length - 1 ? (
          <Button
            type="button"
            className="flex-1"
            disabled={current ? answers[current.code] === undefined : true}
            onClick={() => setStep((s) => s + 1)}
            {...testIdProps(testIds.questionnaires.runnerNext)}
          >
            {t("runner.next")}
          </Button>
        ) : (
          <Button
            type="button"
            className="flex-1"
            disabled={
              submit.isPending ||
              items.some((item) => answers[item.code] === undefined)
            }
            onClick={() => void handleSubmit()}
            {...testIdProps(testIds.questionnaires.runnerSubmit)}
          >
            {t("runner.submit")}
          </Button>
        )}
      </div>
    </div>
  );
}

function StateCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="mx-auto max-w-lg space-y-2 px-4 py-16 text-center">
      <h1 className="text-xl font-semibold">{title}</h1>
      <p className="text-muted-foreground">{body}</p>
    </div>
  );
}
