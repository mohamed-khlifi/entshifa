"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { MEDICAL_UNITS } from "@/lib/i18n/format";
import { testIdProps, testIds } from "@/lib/test/test-id";

type EntHelpersProps = {
  disabled: boolean;
  schedule: readonly string[];
  onAppend: (text: string) => void;
  onPreviewTaper: (input: {
    startMg: string;
    stepMg: string;
    daysPerStep: number;
    minimumMg: string;
  }) => void;
  onApplyTaper: (input: {
    startMg: string;
    stepMg: string;
    daysPerStep: string;
    minimumMg: string;
  }) => void;
};

export function EntHelpers({
  disabled,
  schedule,
  onAppend,
  onPreviewTaper,
  onApplyTaper,
}: EntHelpersProps) {
  const t = useTranslations("prescriptions");
  const [volume, setVolume] = useState("");
  const [frequency, setFrequency] = useState("");
  const [startMg, setStartMg] = useState("");
  const [stepMg, setStepMg] = useState("");
  const [daysPerStep, setDaysPerStep] = useState("");
  const [minimumMg, setMinimumMg] = useState("");
  const frequencyCount = /^\d+$/.test(frequency) ? Number(frequency) : 0;
  const dayCount = /^\d+$/.test(daysPerStep) ? Number(daysPerStep) : 0;

  return (
    <section
      className="space-y-4 rounded-xl border border-border p-4"
      {...testIdProps(testIds.prescriptions.helpers)}
    >
      <h3 className="text-sm font-semibold">{t("helpers.title")}</h3>
      <div className="space-y-2">
        <p className="text-sm font-medium">{t("helpers.saline")}</p>
        <label className="block text-sm">
          {t("helpers.salineVolume")}
          <input
            value={volume}
            onChange={(event) => setVolume(event.target.value)}
            className="mt-1 flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
            {...testIdProps(testIds.prescriptions.salineVolume)}
          />
        </label>
        <label className="block text-sm">
          {t("helpers.salineFrequency")}
          <input
            inputMode="numeric"
            value={frequency}
            onChange={(event) => setFrequency(event.target.value)}
            className="mt-1 flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
            {...testIdProps(testIds.prescriptions.salineFrequency)}
          />
        </label>
        <Button
          type="button"
          variant="secondary"
          disabled={
            disabled || volume.trim().length === 0 || frequencyCount < 1
          }
          onClick={() =>
            onAppend(
              t("helpers.salineText", {
                volume: volume.trim(),
                frequency: frequencyCount,
              }),
            )
          }
          {...testIdProps(testIds.prescriptions.salineApply)}
        >
          {t("helpers.salineApply")}
        </Button>
      </div>
      <div className="flex flex-wrap gap-2">
        <p className="w-full text-sm font-medium">{t("helpers.spray")}</p>
        <p className="w-full text-sm font-medium">{t("helpers.drops")}</p>
        <Button
          type="button"
          variant="secondary"
          disabled={disabled}
          onClick={() => onAppend(t("helpers.sprayText"))}
          {...testIdProps(testIds.prescriptions.sprayApply)}
        >
          {t("helpers.sprayApply")}
        </Button>
        <Button
          type="button"
          variant="secondary"
          disabled={disabled}
          onClick={() => onAppend(t("helpers.dropsText"))}
          {...testIdProps(testIds.prescriptions.dropsApply)}
        >
          {t("helpers.dropsApply")}
        </Button>
      </div>
      <div className="space-y-2">
        <p className="text-sm font-medium">{t("helpers.taper")}</p>
        <label className="block text-sm">
          {t("helpers.taperStart")}
          <input
            value={startMg}
            onChange={(event) => setStartMg(event.target.value)}
            className="mt-1 flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
            {...testIdProps(testIds.prescriptions.taperStart)}
          />
        </label>
        <label className="block text-sm">
          {t("helpers.taperStep")}
          <input
            value={stepMg}
            onChange={(event) => setStepMg(event.target.value)}
            className="mt-1 flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
            {...testIdProps(testIds.prescriptions.taperStep)}
          />
        </label>
        <label className="block text-sm">
          {t("helpers.taperDays")}
          <input
            inputMode="numeric"
            value={daysPerStep}
            onChange={(event) => setDaysPerStep(event.target.value)}
            className="mt-1 flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
            {...testIdProps(testIds.prescriptions.taperDays)}
          />
        </label>
        <label className="block text-sm">
          {t("helpers.taperFloor")}
          <input
            value={minimumMg}
            onChange={(event) => setMinimumMg(event.target.value)}
            className="mt-1 flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
            {...testIdProps(testIds.prescriptions.taperFloor)}
          />
        </label>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="secondary"
            disabled={
              startMg.trim().length === 0 ||
              stepMg.trim().length === 0 ||
              dayCount < 1
            }
            onClick={() =>
              onPreviewTaper({
                startMg: startMg.trim(),
                stepMg: stepMg.trim(),
                daysPerStep: dayCount,
                minimumMg: minimumMg.trim() || "0",
              })
            }
            {...testIdProps(testIds.prescriptions.taperPreview)}
          >
            {t("helpers.taperPreview")}
          </Button>
          <Button
            type="button"
            disabled={disabled || schedule.length === 0}
            onClick={() =>
              onApplyTaper({
                startMg: startMg.trim(),
                stepMg: stepMg.trim(),
                daysPerStep,
                minimumMg: minimumMg.trim() || "0",
              })
            }
            {...testIdProps(testIds.prescriptions.taperApply)}
          >
            {t("helpers.taperApply")}
          </Button>
        </div>
        {schedule.length > 0 ? (
          <div className="space-y-1 text-sm">
            <p>{t("helpers.taperCount", { count: schedule.length })}</p>
            <ol
              className="space-y-1"
              {...testIdProps(testIds.prescriptions.taperSchedule)}
            >
              {schedule.map((dose, index) => (
                <li key={`${index + 1}-${dose}`}>
                  {t("helpers.taperDay", {
                    day: index + 1,
                    dose,
                  })}
                  <span className="sr-only">{MEDICAL_UNITS.mg}</span>
                </li>
              ))}
            </ol>
          </div>
        ) : null}
      </div>
    </section>
  );
}
