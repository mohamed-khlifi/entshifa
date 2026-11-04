"use client";

import { useLocale, useTranslations } from "next-intl";
import { useMemo, useState } from "react";

import {
  useCreateHearingDevice,
  useEvaluateCandidacy,
  usePatientHearingDevices,
} from "../hooks/use-audiology";
import { HEARING_DEVICE_TYPES } from "../constants";
import type {
  HearingDeviceCreate,
  HearingDeviceType,
} from "@/lib/api/generated";
import { formatDate } from "@/lib/i18n/format";
import { Permission } from "@/lib/permissions";
import {
  hearingDeviceRowTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";
import { usePermission } from "@/providers/permission-provider";

type HearingDevicesPanelProps = {
  patientId: string;
  audiogramPublicId: string | null;
};

export function HearingDevicesPanel({
  patientId,
  audiogramPublicId,
}: HearingDevicesPanelProps) {
  const t = useTranslations("audiology");
  const locale = useLocale();
  const canEnter = usePermission(Permission.AUDIOLOGY_ENTER);
  const canInterpret = usePermission(Permission.AUDIOLOGY_INTERPRET);
  const devicesQuery = usePatientHearingDevices(patientId);
  const createDevice = useCreateHearingDevice(patientId);
  const evaluate = useEvaluateCandidacy(patientId);

  const [ear, setEar] = useState<"right" | "left">("right");
  const [deviceType, setDeviceType] = useState<HearingDeviceType>("bte");
  const [fittedOn, setFittedOn] = useState("");
  const [trialCompleted, setTrialCompleted] = useState(false);
  const [imagingClearance, setImagingClearance] = useState(false);
  const [communicationImpact, setCommunicationImpact] = useState(false);

  const evaluation = evaluate.data;

  const sortedDevices = useMemo(() => {
    return [...(devicesQuery.data?.items ?? [])].sort((a, b) =>
      (a.fittedOn ?? "").localeCompare(b.fittedOn ?? ""),
    );
  }, [devicesQuery.data?.items]);

  async function handleCreate() {
    const body: HearingDeviceCreate = {
      patientPublicId: patientId,
      ear,
      deviceType,
      fittedOn: fittedOn.trim() || null,
      status: "active",
    };
    await createDevice.mutateAsync(body);
    setFittedOn("");
  }

  async function handleEvaluate() {
    await evaluate.mutateAsync({
      audiogramPublicId,
      hearingAidTrialCompleted: trialCompleted,
      imagingClearance,
      communicationImpactAssessed: communicationImpact,
    });
  }

  return (
    <section
      className="space-y-4 rounded-lg border border-border p-4"
      {...testIdProps(testIds.audiology.hearingDevicesPanel)}
    >
      <h2 className="text-lg font-semibold">{t("devices.title")}</h2>
      {devicesQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">{t("state.loading")}</p>
      ) : null}
      {devicesQuery.isError ? (
        <p className="text-sm text-destructive">{t("state.error")}</p>
      ) : null}
      <ul
        className="space-y-2"
        {...testIdProps(testIds.audiology.hearingDevicesList)}
      >
        {sortedDevices.length === 0 ? (
          <li className="text-sm text-muted-foreground">
            {t("devices.empty")}
          </li>
        ) : (
          sortedDevices.map((device) => (
            <li
              key={device.publicId}
              className="rounded-md border border-border/60 px-3 py-2 text-sm"
              {...testIdProps(hearingDeviceRowTestId(device.publicId))}
            >
              <span className="font-medium">
                {t(`ear.${device.ear}`)} ·{" "}
                {t(`devices.types.${device.deviceType}`)}
              </span>
              {device.fittedOn ? (
                <span className="text-muted-foreground">
                  {" "}
                  · {formatDate(device.fittedOn, locale)}
                </span>
              ) : null}
              <span className="text-muted-foreground">
                {" "}
                · {t(`devices.status.${device.status}`)}
              </span>
            </li>
          ))
        )}
      </ul>
      {canEnter ? (
        <div
          className="grid gap-3 md:grid-cols-2"
          {...testIdProps(testIds.audiology.hearingDeviceCreateForm)}
        >
          <label className="flex flex-col gap-1 text-sm">
            {t("ear.right")} / {t("ear.left")}
            <select
              value={ear}
              onChange={(event) =>
                setEar(event.target.value as "right" | "left")
              }
              {...testIdProps(testIds.audiology.hearingDeviceEar)}
            >
              <option value="right">{t("ear.right")}</option>
              <option value="left">{t("ear.left")}</option>
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            {t("devices.fields.type")}
            <select
              value={deviceType}
              onChange={(event) =>
                setDeviceType(event.target.value as HearingDeviceType)
              }
              {...testIdProps(testIds.audiology.hearingDeviceType)}
            >
              {HEARING_DEVICE_TYPES.map((value) => (
                <option key={value} value={value}>
                  {t(`devices.types.${value}`)}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            {t("devices.fields.fittedOn")}
            <input
              type="date"
              value={fittedOn}
              onChange={(event) => setFittedOn(event.target.value)}
              {...testIdProps(testIds.audiology.hearingDeviceFittedOn)}
            />
          </label>
          <div className="flex items-end">
            <button
              type="button"
              className="rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
              disabled={createDevice.isPending}
              onClick={() => void handleCreate()}
              {...testIdProps(testIds.audiology.hearingDeviceCreateSubmit)}
            >
              {t("devices.actions.add")}
            </button>
          </div>
        </div>
      ) : null}
      <div
        className="space-y-3 border-t border-border pt-4"
        {...testIdProps(testIds.audiology.candidacyPanel)}
      >
        <h3 className="text-base font-medium">{t("candidacy.title")}</h3>
        {canEnter ? (
          <>
            <div className="flex flex-wrap gap-4 text-sm">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={trialCompleted}
                  onChange={(event) => setTrialCompleted(event.target.checked)}
                  {...testIdProps(testIds.audiology.candidacyTrialCompleted)}
                />
                {t("candidacy.fields.trialCompleted")}
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={imagingClearance}
                  onChange={(event) =>
                    setImagingClearance(event.target.checked)
                  }
                  {...testIdProps(testIds.audiology.candidacyImagingClearance)}
                />
                {t("candidacy.fields.imagingClearance")}
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={communicationImpact}
                  onChange={(event) =>
                    setCommunicationImpact(event.target.checked)
                  }
                  {...testIdProps(
                    testIds.audiology.candidacyCommunicationImpact,
                  )}
                />
                {t("candidacy.fields.communicationImpact")}
              </label>
            </div>
            <button
              type="button"
              className="rounded-full border border-border px-4 py-2 text-sm disabled:opacity-50"
              disabled={evaluate.isPending}
              onClick={() => void handleEvaluate()}
              {...testIdProps(testIds.audiology.candidacyEvaluate)}
            >
              {t("candidacy.actions.evaluate")}
            </button>
          </>
        ) : null}
        {evaluation ? (
          <div
            className="grid gap-2 text-sm md:grid-cols-2"
            {...testIdProps(testIds.audiology.candidacyResults)}
          >
            <p>
              {t("candidacy.hearingAidEligible")}:{" "}
              {evaluation.hearingAidEligible
                ? t("candidacy.eligibleYes")
                : t("candidacy.eligibleNo")}
            </p>
            <p>
              {t("candidacy.cochlearImplantEligible")}:{" "}
              {evaluation.cochlearImplantEligible
                ? t("candidacy.eligibleYes")
                : t("candidacy.eligibleNo")}
            </p>
            {!canInterpret ? (
              <p className="text-muted-foreground md:col-span-2">
                {t("candidacy.confirmRequiresInterpret")}
              </p>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}
