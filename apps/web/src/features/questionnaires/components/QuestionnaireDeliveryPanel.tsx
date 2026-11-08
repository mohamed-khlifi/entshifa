"use client";

import { useLocale, useTranslations } from "next-intl";
import type { UseMutationResult } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { formControlClass } from "@/components/ui/form-control";
import { cn } from "@/lib/utils/cn";
import { Select } from "@/components/ui/select";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { Link } from "@/lib/i18n/navigation";
import { formatDate, formatNumber } from "@/lib/i18n/format";

import type {
  InstrumentSummaryRead,
  QuestionnaireInvitationCreatedRead,
} from "@/lib/api/generated";

import { createQuestionnaireInvitation } from "../api/questionnaires.api";
import {
  useCreateQuestionnaireInvitation,
  useInstrumentsList,
  usePatientQuestionnaireResponses,
} from "../hooks/use-questionnaire-queries";

import { severityBandLabel } from "../lib/labels";
import { QuestionnaireScoreWorkspace } from "./QuestionnaireScoreWorkspace";

type QuestionnaireDeliveryPanelProps = {
  patientId: string;
  defaultInstrumentCode?: string;
};

export function QuestionnaireDeliveryPanel({
  patientId,
  defaultInstrumentCode = "snot22",
}: QuestionnaireDeliveryPanelProps) {
  const t = useTranslations("questionnaires");
  const locale = useLocale();
  const instruments = useInstrumentsList();
  const [instrumentCode, setInstrumentCode] = useState(defaultInstrumentCode);
  const responses = usePatientQuestionnaireResponses(patientId, {
    instrumentCode,
  });
  const createInvite = useCreateQuestionnaireInvitation(patientId);
  const [lastPath, setLastPath] = useState<string | null>(null);

  const launchTablet = () => {
    void createInvite
      .mutateAsync({
        instrumentCode,
        channel: "tablet",
        context: "waiting_room",
        locale,
      })
      .then((row) => {
        if (row.token) {
          setLastPath(row.publicPath);
          window.open(row.publicPath, "_blank", "noopener,noreferrer");
        }
      });
  };

  return (
    <div
      className="space-y-8"
      {...testIdProps(testIds.questionnaires.deliveryPanel)}
    >
      <DeliveryControls
        instrumentCode={instrumentCode}
        setInstrumentCode={setInstrumentCode}
        instruments={instruments.data?.items ?? []}
        launchTablet={launchTablet}
        createInvite={createInvite}
        locale={locale}
        t={t}
        lastPath={lastPath}
      />
      <section
        className="space-y-4"
        {...testIdProps(testIds.questionnaires.historyList)}
      >
        <h3 className="text-sm font-semibold">{t("delivery.historyTitle")}</h3>
        {responses.isLoading ? (
          <p className="text-sm text-muted-foreground">
            {t("delivery.loading")}
          </p>
        ) : null}
        {responses.data?.items.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("delivery.emptyHistory")}
          </p>
        ) : (
          <ul className="space-y-2">
            {responses.data?.items.map((row) => (
              <li
                key={row.publicId}
                className="rounded-md border px-3 py-2 text-sm"
              >
                <HistoryRow row={row} locale={locale} t={t} />
              </li>
            ))}
          </ul>
        )}
      </section>
      <QuestionnaireScoreWorkspace
        patientId={patientId}
        instrumentCode={instrumentCode}
      />
    </div>
  );
}

function DeliveryControls({
  instrumentCode,
  setInstrumentCode,
  instruments,
  launchTablet,
  createInvite,
  locale,
  t,
  lastPath,
}: {
  instrumentCode: string;
  setInstrumentCode: (code: string) => void;
  instruments: InstrumentSummaryRead[];
  launchTablet: () => void;
  createInvite: UseMutationResult<
    QuestionnaireInvitationCreatedRead,
    Error,
    Parameters<typeof createQuestionnaireInvitation>[1]
  >;
  locale: string;
  t: ReturnType<typeof useTranslations<"questionnaires">>;
  lastPath: string | null;
}) {
  return (
    <>
      <div className="flex flex-wrap items-end gap-3">
        <label className="space-y-1 text-sm">
          {t("presentation.instrumentLabel")}
          <Select
            className={cn(formControlClass, "min-w-[12rem]")}
            value={instrumentCode}
            onChange={(event) => setInstrumentCode(event.target.value)}
            {...testIdProps(testIds.questionnaires.instrumentSelect)}
          >
            {instruments.length > 0 ? (
              instruments.map((row) => (
                <option key={row.code} value={row.code}>
                  {row.code}
                </option>
              ))
            ) : (
              <option value={instrumentCode}>{instrumentCode}</option>
            )}
          </Select>
        </label>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          onClick={launchTablet}
          disabled={createInvite.isPending}
          {...testIdProps(testIds.questionnaires.launchTablet)}
        >
          {t("delivery.launchTablet")}
        </Button>
        <Button
          type="button"
          variant="secondary"
          disabled={createInvite.isPending}
          onClick={() =>
            void createInvite.mutateAsync({
              instrumentCode,
              channel: "email",
              context: "pre_visit",
              locale,
            })
          }
          {...testIdProps(testIds.questionnaires.sendInvitation)}
        >
          {t("delivery.sendInvitation")}
        </Button>
      </div>
      {lastPath ? (
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.questionnaires.invitationLink)}
        >
          {t("delivery.linkLabel")}:{" "}
          <Link
            href={lastPath}
            className="text-primary underline-offset-2 hover:underline"
          >
            {t("delivery.launchOpen")}
          </Link>
        </p>
      ) : null}
    </>
  );
}

function HistoryRow({
  row,
  locale,
  t,
}: {
  row: {
    instrumentTitle: string | null;
    instrumentCode: string;
    totalScore: string;
    completedAt: string;
    severityBand: string | null;
    changeFromPrevious: string | null;
    mcidReached: boolean | null;
    enteredBy: string;
  };
  locale: string;
  t: ReturnType<typeof useTranslations<"questionnaires">>;
}) {
  const band = severityBandLabel(t, row.severityBand);
  const delta =
    row.changeFromPrevious !== null && row.changeFromPrevious !== undefined
      ? Number(row.changeFromPrevious)
      : null;
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div>
        <span className="font-medium">
          {row.instrumentTitle ?? row.instrumentCode}
        </span>{" "}
        <span className="tabular-nums">
          {formatNumber(Number(row.totalScore), locale)}
        </span>
        {band ? (
          <span className="ms-2 text-xs text-primary">{band}</span>
        ) : null}
        {delta !== null ? (
          <span className="ms-2 text-xs text-muted-foreground">
            {t("presentation.changeValue", { delta })}
            {row.mcidReached ? ` · ${t("presentation.mcidShort")}` : null}
          </span>
        ) : null}
        <p className="text-xs text-muted-foreground">
          {formatDate(row.completedAt, locale, { dateStyle: "medium" })}
        </p>
      </div>
      <span
        className="rounded bg-muted px-2 py-0.5 text-xs"
        {...testIdProps(testIds.questionnaires.provenanceBadge)}
      >
        {row.enteredBy === "patient"
          ? t("delivery.provenancePatient")
          : row.enteredBy === "clinician"
            ? t("delivery.provenanceClinician")
            : t("delivery.provenanceStaff")}
      </span>
    </div>
  );
}
