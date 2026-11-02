"use client";

import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";

import {
  useInterpretTympanogram,
  usePatientSpeechAudiometry,
  usePatientTympanograms,
  useSaveSpeechAudiometry,
  useSaveTympanogram,
} from "../hooks/use-audiology";
import {
  configurationLabel,
  earLabel,
  etfLabel,
  jergerLabel,
  lossTypeLabel,
} from "../lib/labels";
import { latestByEar } from "../utils/dashboard.utils";
import type { AudiogramRead } from "@/lib/api/generated";
import { Permission } from "@/lib/permissions";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { usePermission } from "@/providers/permission-provider";

type TympanogramPanelProps = {
  patientId: string;
  audiogram: AudiogramRead | null;
};

const JERGER_TYPES = ["A", "As", "Ad", "B", "C"] as const;

export function TympanogramPanel({
  patientId,
  audiogram,
}: TympanogramPanelProps) {
  const t = useTranslations("audiology");
  const canEnter = usePermission(Permission.AUDIOLOGY_ENTER);
  const canInterpret = usePermission(Permission.AUDIOLOGY_INTERPRET);
  const tympQuery = usePatientTympanograms(patientId);
  const speechQuery = usePatientSpeechAudiometry(patientId);
  const saveTymp = useSaveTympanogram(patientId);
  const saveSpeech = useSaveSpeechAudiometry(patientId);
  const interpretTymp = useInterpretTympanogram(patientId);
  const [tympIdempotency] = useState(() => crypto.randomUUID());
  const [speechIdempotency] = useState(() => crypto.randomUUID());

  const tympByEar = useMemo(
    () => latestByEar(tympQuery.data?.items ?? []),
    [tympQuery.data?.items],
  );
  const speechByEar = useMemo(
    () => latestByEar(speechQuery.data?.items ?? []),
    [speechQuery.data?.items],
  );

  return (
    <div
      className="grid gap-4 lg:grid-cols-2"
      {...testIdProps(testIds.audiology.tympanogramPanel)}
    >
      {(["right", "left"] as const).map((ear) => {
        const tymp = tympByEar[ear];
        const speech = speechByEar[ear];
        const jergerTestId =
          ear === "right"
            ? testIds.audiology.tympJergerRight
            : testIds.audiology.tympJergerLeft;
        const lossType =
          ear === "right" ? audiogram?.lossTypeRight : audiogram?.lossTypeLeft;
        const configuration =
          ear === "right"
            ? audiogram?.configurationRight
            : audiogram?.configurationLeft;
        return (
          <section
            key={ear}
            className="space-y-3 rounded-xl border border-border bg-muted/10 p-4"
          >
            <h3 className="text-sm font-semibold">{earLabel(t, ear)}</h3>
            <div className="space-y-1 text-sm">
              <p>
                {t("tympanometry.summary", {
                  jerger: jergerLabel(t, tymp?.jergerType ?? null),
                  peak: tymp?.peakPressureDapa ?? "—",
                  compliance: tymp?.complianceMl ?? "—",
                })}
              </p>
              {tymp?.etfResult ? (
                <p>
                  {t("tympanometry.etf", {
                    value: etfLabel(t, tymp.etfResult),
                  })}
                </p>
              ) : null}
            </div>
            <div className="space-y-1 text-sm">
              <h4 className="font-medium">{t("speech.title")}</h4>
              <p>
                {t("speech.summary", {
                  srt: speech?.srtDb ?? "—",
                  wrs: speech?.wrsPercent ?? "—",
                })}
              </p>
            </div>
            {audiogram ? (
              <p className="text-xs text-muted-foreground">
                {t("dashboard.earMetricsLine", {
                  loss: lossTypeLabel(t, lossType ?? null),
                  configuration: configurationLabel(t, configuration ?? null),
                })}
              </p>
            ) : null}
            {canEnter && !tymp ? (
              <button
                type="button"
                className="rounded-full border border-border px-3 py-1 text-xs"
                disabled={saveTymp.isPending}
                onClick={() => {
                  void saveTymp.mutateAsync({
                    tympanogramId: null,
                    createBody: {
                      patientPublicId: patientId,
                      ear,
                      probeToneHz: 226,
                    },
                    updateBody: { version: 1 },
                    idempotencyKey: tympIdempotency,
                  });
                }}
              >
                {t("tympanometry.create")}
              </button>
            ) : null}
            {canEnter ? (
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-full border border-border px-3 py-1 text-xs"
                  disabled={saveTymp.isPending || !tymp}
                  onClick={() => {
                    if (!tymp) {
                      return;
                    }
                    void saveTymp.mutateAsync({
                      tympanogramId: tymp.publicId,
                      createBody: {
                        patientPublicId: patientId,
                        ear,
                        probeToneHz: 226,
                      },
                      updateBody: {
                        peakPressureDapa: tymp.peakPressureDapa,
                        complianceMl: tymp.complianceMl,
                        ecvMl: tymp.ecvMl,
                        version: tymp.version,
                      },
                      idempotencyKey: tympIdempotency,
                    });
                  }}
                >
                  {t("tympanometry.save")}
                </button>
                <button
                  type="button"
                  className="rounded-full border border-border px-3 py-1 text-xs"
                  disabled={saveSpeech.isPending}
                  onClick={() => {
                    void saveSpeech.mutateAsync({
                      speechId: speech?.publicId ?? null,
                      createBody: {
                        patientPublicId: patientId,
                        ear,
                        audiogramPublicId: audiogram?.publicId ?? null,
                        srtDb: speech?.srtDb ?? null,
                        wrsPercent: speech?.wrsPercent ?? null,
                        wrsLevelDb: speech?.wrsLevelDb ?? null,
                      },
                      updateBody: {
                        audiogramPublicId: audiogram?.publicId ?? null,
                        srtDb: speech?.srtDb ?? null,
                        wrsPercent: speech?.wrsPercent ?? null,
                        wrsLevelDb: speech?.wrsLevelDb ?? null,
                        version: speech?.version ?? 1,
                      },
                      idempotencyKey: speechIdempotency,
                    });
                  }}
                >
                  {t("speech.save")}
                </button>
              </div>
            ) : null}
            {canInterpret && tymp ? (
              <label className="block space-y-1 text-xs">
                {t("tympanometry.jergerOverride")}
                <select
                  className="h-9 w-full rounded-lg border border-input bg-card px-2"
                  value={tymp.jergerType ?? ""}
                  disabled={interpretTymp.isPending}
                  onChange={(event) => {
                    const jergerType = event.target
                      .value as (typeof JERGER_TYPES)[number];
                    if (!jergerType) {
                      return;
                    }
                    void interpretTymp.mutateAsync({
                      tympanogramId: tymp.publicId,
                      body: {
                        jergerType,
                        version: tymp.version,
                      },
                    });
                  }}
                  {...testIdProps(jergerTestId)}
                >
                  <option value="">{t("tympanometry.jergerUnknown")}</option>
                  {JERGER_TYPES.map((value) => (
                    <option key={value} value={value}>
                      {jergerLabel(t, value)}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
          </section>
        );
      })}
    </div>
  );
}
