"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { Link } from "@/lib/i18n/navigation";

import {
  useCreateQuestionnaireInvitation,
  usePatientQuestionnaireResponses,
} from "../hooks/use-questionnaire-queries";

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
  const responses = usePatientQuestionnaireResponses(patientId);
  const createInvite = useCreateQuestionnaireInvitation(patientId);
  const [lastPath, setLastPath] = useState<string | null>(null);

  const launchTablet = () => {
    void createInvite
      .mutateAsync({
        instrumentCode: defaultInstrumentCode,
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
      className="space-y-6"
      {...testIdProps(testIds.questionnaires.deliveryPanel)}
    >
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
              instrumentCode: defaultInstrumentCode,
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
      <section
        className="space-y-2"
        {...testIdProps(testIds.questionnaires.historyList)}
      >
        <h3 className="text-sm font-semibold">{t("delivery.historyTitle")}</h3>
        {responses.isLoading ? (
          <p className="text-sm text-muted-foreground">…</p>
        ) : null}
        {responses.data?.items.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("delivery.emptyHistory")}
          </p>
        ) : null}
        <ul className="space-y-2">
          {responses.data?.items.map((row) => (
            <li
              key={row.publicId}
              className="rounded-md border px-3 py-2 text-sm"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span>
                  {row.instrumentTitle ?? row.instrumentCode} — {row.totalScore}
                </span>
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
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
