"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";

import {
  useCreateOmeEpisode,
  usePediatricAudiologySummary,
  useUpdateNewbornScreening,
  useUpdatePediatricMilestones,
} from "../hooks/use-audiology";
import { NEWBORN_SCREEN_RESULTS, PEDIATRIC_MILESTONE_KEYS } from "../constants";
import type {
  NewbornScreeningUpdate,
  OmeLaterality,
} from "@/lib/api/generated";
import { formatDate } from "@/lib/i18n/format";
import { Permission } from "@/lib/permissions";
import {
  omeEpisodeRowTestId,
  pediatricMilestoneTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";
import { usePermission } from "@/providers/permission-provider";

type PediatricAudiologyPanelProps = {
  patientId: string;
  audiogramPublicId: string | null;
};

export function PediatricAudiologyPanel({
  patientId,
  audiogramPublicId,
}: PediatricAudiologyPanelProps) {
  const t = useTranslations("audiology");
  const locale = useLocale();
  const canEnter = usePermission(Permission.AUDIOLOGY_ENTER);
  const summaryQuery = usePediatricAudiologySummary(patientId);
  const updateScreening = useUpdateNewbornScreening(patientId);
  const updateMilestones = useUpdatePediatricMilestones(patientId);
  const createOme = useCreateOmeEpisode(patientId);

  const pediatric = summaryQuery.data?.pediatric ?? null;
  const omeEpisodes = summaryQuery.data?.omeEpisodes ?? [];

  const [screenDate, setScreenDate] = useState("");
  const [screenRight, setScreenRight] = useState<
    (typeof NEWBORN_SCREEN_RESULTS)[number] | ""
  >("");
  const [screenLeft, setScreenLeft] = useState<
    (typeof NEWBORN_SCREEN_RESULTS)[number] | ""
  >("");
  const [milestones, setMilestones] = useState<Record<string, boolean>>({});
  const [omeLaterality, setOmeLaterality] =
    useState<OmeLaterality>("bilateral");
  const [omeFirstSeen, setOmeFirstSeen] = useState("");
  const [omeHearingDb, setOmeHearingDb] = useState("");

  useEffect(() => {
    if (!pediatric) {
      return;
    }
    setScreenDate(pediatric.screenDate ?? "");
    setScreenRight(pediatric.screenResultRight ?? "");
    setScreenLeft(pediatric.screenResultLeft ?? "");
    const next: Record<string, boolean> = {};
    for (const key of PEDIATRIC_MILESTONE_KEYS) {
      next[key] = pediatric.speechLanguageMilestones?.[key] ?? false;
    }
    setMilestones(next);
  }, [pediatric]);

  const ehdiRows = useMemo(() => {
    if (!pediatric) {
      return [];
    }
    return [
      {
        key: "screenBy1m" as const,
        status: pediatric.screenBy1MStatus,
      },
      {
        key: "diagnosisBy3m" as const,
        status: pediatric.diagnosisBy3MStatus,
      },
      {
        key: "interventionBy6m" as const,
        status: pediatric.interventionBy6MStatus,
      },
    ];
  }, [pediatric]);

  async function saveScreening() {
    const body: NewbornScreeningUpdate = {
      screenDate: screenDate.trim() || null,
      screenResultRight: screenRight || null,
      screenResultLeft: screenLeft || null,
    };
    await updateScreening.mutateAsync(body);
  }

  async function saveMilestones() {
    await updateMilestones.mutateAsync({ milestones });
  }

  async function startOmeWatchfulWaiting() {
    if (!omeFirstSeen.trim()) {
      return;
    }
    await createOme.mutateAsync({
      patientPublicId: patientId,
      audiogramPublicId,
      laterality: omeLaterality,
      firstSeenOn: omeFirstSeen,
      hearingLevelDb: omeHearingDb.trim()
        ? Number.parseFloat(omeHearingDb)
        : null,
    });
    setOmeFirstSeen("");
    setOmeHearingDb("");
  }

  return (
    <section
      className="space-y-4 rounded-lg border border-border p-4"
      {...testIdProps(testIds.audiology.pediatricPanel)}
    >
      <h2 className="text-lg font-semibold">{t("pediatric.title")}</h2>
      {summaryQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">{t("state.loading")}</p>
      ) : null}
      {summaryQuery.isError ? (
        <p className="text-sm text-destructive">{t("state.error")}</p>
      ) : null}

      <div {...testIdProps(testIds.audiology.ehdiBenchmarks)}>
        <h3 className="text-base font-medium">{t("pediatric.ehdiTitle")}</h3>
        {ehdiRows.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("pediatric.ehdiEmpty")}
          </p>
        ) : (
          <ul className="mt-2 space-y-1 text-sm">
            {ehdiRows.map((row) => (
              <li key={row.key}>
                {t(`pediatric.ehdi.${row.key}`)}:{" "}
                {t(`pediatric.ehdiStatus.${row.status}`)}
              </li>
            ))}
          </ul>
        )}
      </div>

      {canEnter ? (
        <div
          className="grid gap-3 md:grid-cols-2"
          {...testIdProps(testIds.audiology.newbornScreeningForm)}
        >
          <h3 className="md:col-span-2 text-base font-medium">
            {t("pediatric.screeningTitle")}
          </h3>
          <label className="flex flex-col gap-1 text-sm">
            {t("pediatric.fields.screenDate")}
            <input
              type="date"
              value={screenDate}
              onChange={(event) => setScreenDate(event.target.value)}
              {...testIdProps(testIds.audiology.screenDate)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            {t("pediatric.fields.screenResultRight")}
            <select
              value={screenRight}
              onChange={(event) =>
                setScreenRight(
                  event.target.value as
                    (typeof NEWBORN_SCREEN_RESULTS)[number] | "",
                )
              }
              {...testIdProps(testIds.audiology.screenResultRight)}
            >
              <option value="">{t("pediatric.notRecorded")}</option>
              {NEWBORN_SCREEN_RESULTS.map((value) => (
                <option key={value} value={value}>
                  {t(`pediatric.screenResults.${value}`)}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            {t("pediatric.fields.screenResultLeft")}
            <select
              value={screenLeft}
              onChange={(event) =>
                setScreenLeft(
                  event.target.value as
                    (typeof NEWBORN_SCREEN_RESULTS)[number] | "",
                )
              }
              {...testIdProps(testIds.audiology.screenResultLeft)}
            >
              <option value="">{t("pediatric.notRecorded")}</option>
              {NEWBORN_SCREEN_RESULTS.map((value) => (
                <option key={value} value={value}>
                  {t(`pediatric.screenResults.${value}`)}
                </option>
              ))}
            </select>
          </label>
          <div className="flex items-end md:col-span-2">
            <button
              type="button"
              className="rounded-full border border-border px-4 py-2 text-sm disabled:opacity-50"
              disabled={updateScreening.isPending}
              onClick={() => void saveScreening()}
              {...testIdProps(testIds.audiology.screeningSave)}
            >
              {t("pediatric.actions.saveScreening")}
            </button>
          </div>
        </div>
      ) : null}

      <div {...testIdProps(testIds.audiology.milestonesForm)}>
        <h3 className="text-base font-medium">
          {t("pediatric.milestonesTitle")}
        </h3>
        <ul className="mt-2 space-y-2">
          {PEDIATRIC_MILESTONE_KEYS.map((key) => (
            <li key={key}>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  disabled={!canEnter}
                  checked={milestones[key] ?? false}
                  onChange={(event) =>
                    setMilestones((current) => ({
                      ...current,
                      [key]: event.target.checked,
                    }))
                  }
                  {...testIdProps(pediatricMilestoneTestId(key))}
                />
                {t(`pediatric.milestones.${key}`)}
              </label>
            </li>
          ))}
        </ul>
        {canEnter ? (
          <button
            type="button"
            className="mt-3 rounded-full border border-border px-4 py-2 text-sm disabled:opacity-50"
            disabled={updateMilestones.isPending}
            onClick={() => void saveMilestones()}
            {...testIdProps(testIds.audiology.milestonesSave)}
          >
            {t("pediatric.actions.saveMilestones")}
          </button>
        ) : null}
      </div>

      <div {...testIdProps(testIds.audiology.omePanel)}>
        <h3 className="text-base font-medium">{t("pediatric.omeTitle")}</h3>
        <ul className="mt-2 space-y-2 text-sm">
          {omeEpisodes.length === 0 ? (
            <li className="text-muted-foreground">{t("pediatric.omeEmpty")}</li>
          ) : (
            omeEpisodes.map((episode) => (
              <li
                key={episode.publicId}
                className="rounded-md border border-border/60 px-3 py-2"
                {...testIdProps(omeEpisodeRowTestId(episode.publicId))}
              >
                {t(`pediatric.omeLaterality.${episode.laterality}`)} ·{" "}
                {formatDate(episode.firstSeenOn, locale)} ·{" "}
                {t(`pediatric.omeStatus.${episode.status}`)} ·{" "}
                {t("pediatric.omeDue")}{" "}
                {formatDate(episode.watchfulWaitingDueOn, locale)}
              </li>
            ))
          )}
        </ul>
        {canEnter ? (
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <label className="flex flex-col gap-1 text-sm">
              {t("pediatric.fields.omeLaterality")}
              <select
                value={omeLaterality}
                onChange={(event) =>
                  setOmeLaterality(event.target.value as OmeLaterality)
                }
                {...testIdProps(testIds.audiology.omeLaterality)}
              >
                <option value="right">{t("ear.right")}</option>
                <option value="left">{t("ear.left")}</option>
                <option value="bilateral">
                  {t("pediatric.omeLaterality.bilateral")}
                </option>
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm">
              {t("pediatric.fields.omeFirstSeen")}
              <input
                type="date"
                value={omeFirstSeen}
                onChange={(event) => setOmeFirstSeen(event.target.value)}
                {...testIdProps(testIds.audiology.omeFirstSeen)}
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              {t("pediatric.fields.omeHearingDb")}
              <input
                type="number"
                min={-10}
                max={130}
                step={5}
                value={omeHearingDb}
                onChange={(event) => setOmeHearingDb(event.target.value)}
                {...testIdProps(testIds.audiology.omeHearingDb)}
              />
            </label>
            <div className="flex items-end">
              <button
                type="button"
                className="rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
                disabled={createOme.isPending}
                onClick={() => void startOmeWatchfulWaiting()}
                {...testIdProps(testIds.audiology.omeCreateSubmit)}
              >
                {t("pediatric.actions.startOme")}
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
