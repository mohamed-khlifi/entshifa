"use client";

import { useLocale, useTranslations } from "next-intl";
import { useMemo, useState } from "react";

import { AudiogramChart } from "./AudiogramChart/AudiogramChart";
import { ComparisonOverlay } from "./ComparisonOverlay";
import { ThresholdEvolutionChart } from "./ThresholdEvolutionChart";
import { TympanogramPanel } from "./TympanogramPanel";
import { STANDARD_FREQUENCIES_HZ } from "../constants";
import {
  usePatientAbrResults,
  usePatientSpeechAudiometry,
  usePatientTympanograms,
} from "../hooks/use-audiology";
import {
  configurationLabel,
  earLabel,
  lossTypeLabel,
  ptaFormulaLabel,
  whoGradeLabel,
} from "../lib/labels";
import type { OverlaySeries } from "../types/audiology.types";
import {
  buildFrequencyEvolutionSeries,
  filterOverlaysByEar,
  filterPointsByEar,
  latestByEar,
} from "../utils/dashboard.utils";
import {
  frequenciesForChart,
  hasExtendedHighFrequencies,
  thresholdsToChartPoints,
} from "../utils/audiogram.utils";
import type { AudiogramRead } from "@/lib/api/generated";
import { formatDate } from "@/lib/i18n/format";
import {
  audiogramThumbnailTestId,
  evolutionFrequencyTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

type ChartLayout = "sideBySide" | "overlay";

type AudiologyDashboardProps = {
  patientId: string;
  audiogram: AudiogramRead | null;
  history: readonly AudiogramRead[];
  overlayCandidates: OverlaySeries[];
  overlayIds: ReadonlySet<string>;
  onToggleOverlay: (publicId: string) => void;
};

const EVOLUTION_FREQUENCIES = [500, 1000, 2000, 4000] as const;

export function AudiologyDashboard({
  patientId,
  audiogram,
  history,
  overlayCandidates,
  overlayIds,
  onToggleOverlay,
}: AudiologyDashboardProps) {
  const t = useTranslations("audiology");
  const locale = useLocale();
  const [layout, setLayout] = useState<ChartLayout>("sideBySide");
  const [evolutionHz, setEvolutionHz] = useState<number>(1000);
  const speechQuery = usePatientSpeechAudiometry(patientId);
  const tympQuery = usePatientTympanograms(patientId);
  const abrQuery = usePatientAbrResults(patientId);

  const frequencies = useMemo(() => {
    if (!audiogram) {
      return [...STANDARD_FREQUENCIES_HZ];
    }
    return frequenciesForChart(
      audiogram.hasExtendedHighFrequencies ||
        hasExtendedHighFrequencies(audiogram.thresholds),
    );
  }, [audiogram]);

  const points = useMemo(() => {
    if (!audiogram) {
      return [];
    }
    return thresholdsToChartPoints(audiogram.thresholds);
  }, [audiogram]);

  const overlays: OverlaySeries[] = useMemo(() => {
    return overlayCandidates.filter((row) => overlayIds.has(row.publicId));
  }, [overlayCandidates, overlayIds]);

  const evolutionSamples = useMemo(
    () => buildFrequencyEvolutionSeries(history, evolutionHz, "air", false),
    [evolutionHz, history],
  );

  const speechByEar = useMemo(
    () => latestByEar(speechQuery.data?.items ?? []),
    [speechQuery.data?.items],
  );
  const tympByEar = useMemo(
    () => latestByEar(tympQuery.data?.items ?? []),
    [tympQuery.data?.items],
  );

  const alerts = useMemo(() => {
    if (!audiogram) {
      return {
        asymmetry: false,
        shift: false,
        speechDiscrepancy: false,
        largeCanal: false,
        abrWaveV: false,
      };
    }
    const speechDiscrepancy =
      speechByEar.right?.speechPtaDiscrepancyFlag ||
      speechByEar.left?.speechPtaDiscrepancyFlag ||
      false;
    const largeCanal =
      tympByEar.right?.largeCanalVolumeFlag ||
      tympByEar.left?.largeCanalVolumeFlag ||
      false;
    const abrWaveV = (abrQuery.data?.items ?? []).some(
      (row) => row.interauralVFlag,
    );
    return {
      asymmetry: audiogram.asymmetryFlag,
      shift: audiogram.shiftFlag,
      speechDiscrepancy,
      largeCanal,
      abrWaveV,
    };
  }, [abrQuery.data?.items, audiogram, speechByEar, tympByEar]);

  if (!audiogram) {
    return (
      <p
        className="text-sm text-muted-foreground"
        {...testIdProps(testIds.audiology.dashboard)}
      >
        {t("dashboard.selectAudiogram")}
      </p>
    );
  }

  return (
    <div
      className="space-y-6 print:hidden"
      {...testIdProps(testIds.audiology.dashboard)}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium">
          {t("dashboard.layoutTitle")}
        </span>
        <button
          type="button"
          className={`rounded-full px-3 py-1 text-sm ${
            layout === "sideBySide"
              ? "bg-primary/10 text-primary"
              : "border border-border text-muted-foreground"
          }`}
          onClick={() => setLayout("sideBySide")}
          {...testIdProps(testIds.audiology.layoutSideBySide)}
        >
          {t("dashboard.layoutSideBySide")}
        </button>
        <button
          type="button"
          className={`rounded-full px-3 py-1 text-sm ${
            layout === "overlay"
              ? "bg-primary/10 text-primary"
              : "border border-border text-muted-foreground"
          }`}
          onClick={() => setLayout("overlay")}
          {...testIdProps(testIds.audiology.layoutOverlay)}
        >
          {t("dashboard.layoutOverlay")}
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {(["right", "left"] as const).map((ear) => {
          const pta = ear === "right" ? audiogram.ptaRight : audiogram.ptaLeft;
          const grade =
            ear === "right" ? audiogram.gradeRight : audiogram.gradeLeft;
          const abg = ear === "right" ? audiogram.abgRight : audiogram.abgLeft;
          const loss =
            ear === "right" ? audiogram.lossTypeRight : audiogram.lossTypeLeft;
          const config =
            ear === "right"
              ? audiogram.configurationRight
              : audiogram.configurationLeft;
          return (
            <article
              key={ear}
              className={`space-y-2 rounded-xl border p-4 ${
                ear === "right"
                  ? "border-red-200 bg-red-50/40 dark:border-red-900/40 dark:bg-red-950/20"
                  : "border-blue-200 bg-blue-50/40 dark:border-blue-900/40 dark:bg-blue-950/20"
              }`}
              {...testIdProps(
                ear === "right"
                  ? testIds.audiology.earCardRight
                  : testIds.audiology.earCardLeft,
              )}
            >
              <h3 className="text-sm font-semibold">{earLabel(t, ear)}</h3>
              <p className="text-3xl font-bold tabular-nums">
                {pta !== null ? `${pta} dB HL` : "—"}
              </p>
              <p className="text-lg font-semibold">{whoGradeLabel(t, grade)}</p>
              <p className="text-sm text-muted-foreground">
                {ptaFormulaLabel(t, audiogram.ptaFormula)}
              </p>
              {loss ? (
                <p className="text-sm">
                  {t("metrics.lossType", {
                    ear: earLabel(t, ear),
                    value: lossTypeLabel(t, loss),
                  })}
                </p>
              ) : null}
              {config ? (
                <p className="text-sm">
                  {t("metrics.configuration", {
                    ear: earLabel(t, ear),
                    value: configurationLabel(t, config),
                  })}
                </p>
              ) : null}
              {abg !== null ? (
                <p className="text-sm">
                  {t("metrics.abg", {
                    ear: earLabel(t, ear),
                    value: abg,
                  })}
                </p>
              ) : null}
            </article>
          );
        })}
      </div>

      <div
        className="flex flex-wrap gap-2"
        {...testIdProps(testIds.audiology.alertsRow)}
      >
        {alerts.asymmetry ? (
          <span
            className="rounded-full bg-amber-100 px-3 py-1 text-xs text-amber-900 dark:bg-amber-950 dark:text-amber-100"
            {...testIdProps(testIds.audiology.alertAsymmetry)}
          >
            {t("alerts.asymmetry")}
          </span>
        ) : null}
        {alerts.shift ? (
          <span
            className="rounded-full bg-amber-100 px-3 py-1 text-xs text-amber-900 dark:bg-amber-950 dark:text-amber-100"
            {...testIdProps(testIds.audiology.alertShift)}
          >
            {t("alerts.shift")}
          </span>
        ) : null}
        {alerts.speechDiscrepancy ? (
          <span
            className="rounded-full bg-amber-100 px-3 py-1 text-xs text-amber-900 dark:bg-amber-950 dark:text-amber-100"
            {...testIdProps(testIds.audiology.alertSpeechDiscrepancy)}
          >
            {t("alerts.speechDiscrepancy")}
          </span>
        ) : null}
        {alerts.largeCanal ? (
          <span
            className="rounded-full bg-amber-100 px-3 py-1 text-xs text-amber-900 dark:bg-amber-950 dark:text-amber-100"
            {...testIdProps(testIds.audiology.alertLargeCanal)}
          >
            {t("alerts.largeCanal")}
          </span>
        ) : null}
        {alerts.abrWaveV ? (
          <span
            className="rounded-full bg-amber-100 px-3 py-1 text-xs text-amber-900 dark:bg-amber-950 dark:text-amber-100"
            {...testIdProps(testIds.audiology.alertAbrWaveV)}
          >
            {t("alerts.abrWaveV")}
          </span>
        ) : null}
      </div>

      <div dir="ltr" className="space-y-4">
        {layout === "overlay" ? (
          <AudiogramChart
            frequencies={frequencies}
            points={points}
            overlays={overlays}
            readOnly
            activeEar="right"
            activeConduction="air"
            activeMasked={false}
            onPlot={() => undefined}
          />
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {(["right", "left"] as const).map((ear) => (
              <div
                key={ear}
                {...testIdProps(
                  ear === "right"
                    ? testIds.audiology.chartRight
                    : testIds.audiology.chartLeft,
                )}
              >
                <p className="mb-2 text-sm font-medium">{earLabel(t, ear)}</p>
                <AudiogramChart
                  frequencies={frequencies}
                  points={filterPointsByEar(points, ear)}
                  overlays={filterOverlaysByEar(overlays, ear)}
                  readOnly
                  activeEar={ear}
                  activeConduction="air"
                  activeMasked={false}
                  onPlot={() => undefined}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      <TympanogramPanel patientId={patientId} audiogram={audiogram} />

      <ComparisonOverlay
        overlays={overlayCandidates}
        selectedIds={overlayIds}
        onToggle={onToggleOverlay}
      />

      <section
        className="space-y-2"
        {...testIdProps(testIds.audiology.historyStrip)}
      >
        <h3 className="text-sm font-semibold">{t("dashboard.historyTitle")}</h3>
        <ul className="flex flex-wrap gap-3">
          {history
            .filter((row) => row.publicId !== audiogram.publicId)
            .map((row) => {
              const miniFreq = frequenciesForChart(
                row.hasExtendedHighFrequencies ||
                  hasExtendedHighFrequencies(row.thresholds),
              );
              const miniPoints = thresholdsToChartPoints(row.thresholds);
              const active = overlayIds.has(row.publicId);
              return (
                <li key={row.publicId}>
                  <button
                    type="button"
                    className={`space-y-1 rounded-lg border p-2 text-left ${
                      active ? "border-primary bg-primary/5" : "border-border"
                    }`}
                    onClick={() => {
                      onToggleOverlay(row.publicId);
                    }}
                    {...testIdProps(audiogramThumbnailTestId(row.publicId))}
                  >
                    <span className="block text-xs text-muted-foreground">
                      {formatDate(row.performedAt, locale)}
                    </span>
                    <div className="h-16 w-28 overflow-hidden" dir="ltr">
                      <AudiogramChart
                        frequencies={miniFreq}
                        points={miniPoints}
                        overlays={[]}
                        readOnly
                        activeEar="right"
                        activeConduction="air"
                        activeMasked={false}
                        onPlot={() => undefined}
                      />
                    </div>
                  </button>
                </li>
              );
            })}
        </ul>
      </section>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium">
          {t("dashboard.evolutionFrequency")}
        </span>
        <select
          className="h-9 rounded-lg border border-input bg-card px-2 text-sm"
          value={evolutionHz}
          onChange={(event) => setEvolutionHz(Number(event.target.value))}
          {...testIdProps(testIds.audiology.evolutionFrequency)}
        >
          {EVOLUTION_FREQUENCIES.map((hz) => (
            <option
              key={hz}
              value={hz}
              {...testIdProps(evolutionFrequencyTestId(hz))}
            >
              {hz} Hz
            </option>
          ))}
        </select>
      </div>
      <ThresholdEvolutionChart samples={evolutionSamples} locale={locale} />

      {audiogram.interpretationText ? (
        <blockquote className="rounded-lg border border-border bg-muted/20 p-4 text-sm">
          {audiogram.interpretationText}
        </blockquote>
      ) : null}
    </div>
  );
}
