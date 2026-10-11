"use client";

import { useLocale, useTranslations } from "next-intl";
import { cloneElement, useEffect, useMemo, useRef, useState } from "react";
import type { InputHTMLAttributes, ReactElement } from "react";

import { OtologyProcedureForm } from "./OtologyProcedureForm";
import {
  findingMembers,
  usePatientEarDevices,
  usePatientOtologyExams,
  useOtologyValueSet,
  useSaveOtology,
  useSignOtology,
  useUpdateEarDevice,
} from "../hooks/use-otology";
import {
  DEVICE_STATUSES,
  FORKS,
  LATERALITIES,
  METHODS,
  MOBILITY,
  RINNE,
  WEBER,
  applyMapFinding,
  applyMapNormal,
  applyMapNotExamined,
  draftFromExam,
  draftIssues,
  emptyDraft,
  marksForSide,
  openTubeDevices,
  toWrite,
  type OtologyDraft,
} from "../lib/draft";
import { lateralityLabel, methodLabel, optionLabel } from "../lib/labels";
import { useCurrentClinicQuery } from "@/features/clinics";
import { AnatomicalMap } from "@/components/clinical/AnatomicalMap/AnatomicalMap";
import type { MapFindingOption, MapSide } from "@/lib/anatomy/types";
import { tympanicMembraneMap } from "@/lib/anatomy/tympanic-membrane.map";
import { isoToDateTimeLocal } from "../lib/clock";
import type { EarDeviceRead } from "@/lib/api/generated";
import {
  otologyDeviceStatusTestId,
  otologyExamTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

const HIDDEN_FINDINGS = new Set([
  "FIND.TM.NOT_VISUALIZED",
  "FIND.TM.UNKNOWN",
  "FIND.CANAL.NOT_VISUALIZED",
  "FIND.CANAL.UNKNOWN",
]);

type OtologyWorkspaceProps = {
  patientId: string;
  examId: string | null;
  onExamChange: (examId: string | null) => void;
};

export function OtologyWorkspace({
  patientId,
  examId,
  onExamChange,
}: OtologyWorkspaceProps) {
  const t = useTranslations("otology");
  const locale = useLocale();
  const contentLocale = locale === "fr" || locale === "ar" ? locale : "en";
  const clinic = useCurrentClinicQuery();
  const timeZone = clinic.data?.timezone ?? "UTC";
  const exams = usePatientOtologyExams(patientId);
  const devices = usePatientEarDevices(patientId);
  const membrane = useOtologyValueSet("tm.findings");
  const canal = useOtologyValueSet("tm.canal.findings");
  const save = useSaveOtology(patientId);
  const sign = useSignOtology(patientId);
  const updateDevice = useUpdateEarDevice(patientId);
  const [draft, setDraft] = useState<OtologyDraft>(() =>
    emptyDraft(localNow()),
  );
  const [baseline, setBaseline] = useState<string | null>(null);
  const [side, setSide] = useState<MapSide>("right");
  const [confirmingSign, setConfirmingSign] = useState(false);
  const [issues, setIssues] = useState<string[]>([]);
  const loadedKey = useRef<string | null>(null);
  const selected = exams.data?.items.find((row) => row.publicId === examId);
  const readOnly = draft.procedureStatus !== "draft";
  const dirty = baseline !== null && JSON.stringify(draft) !== baseline;

  useEffect(() => {
    if (clinic.isLoading) {
      return;
    }
    const key = selected
      ? `${selected.publicId}:${selected.version}:${timeZone}`
      : examId
        ? "pending"
        : `new:${timeZone}`;
    if (loadedKey.current === key) {
      return;
    }
    loadedKey.current = key;
    if (!selected) {
      if (examId) {
        return;
      }
      const next = emptyDraft(localNow());
      setDraft(next);
      setBaseline(JSON.stringify(next));
      setIssues([]);
      return;
    }
    const next = draftFromExam(
      selected,
      isoToDateTimeLocal(selected.performedAt, timeZone),
    );
    setDraft(next);
    setBaseline(JSON.stringify(next));
    setIssues([]);
  }, [clinic.isLoading, examId, selected, timeZone]);

  const persistLatest = useRef<(silent: boolean) => Promise<void>>(
    async () => undefined,
  );

  useEffect(() => {
    if (!dirty || readOnly || !draft.version) {
      return;
    }
    const handle = window.setTimeout(() => {
      void persistLatest.current(true);
    }, 2000);
    return () => window.clearTimeout(handle);
  }, [dirty, draft, readOnly]);

  const findingsByValueSet = useMemo(
    () => ({
      "tm.findings": options(findingMembers(membrane.data)),
      "tm.canal.findings": options(findingMembers(canal.data)),
    }),
    [membrane.data, canal.data],
  );

  async function persist(silent: boolean) {
    const found = draftIssues(draft);
    if (found.length > 0) {
      if (!silent) {
        setIssues(found);
      }
      return;
    }
    const body = toWrite(draft, patientId, timeZone, contentLocale);
    if (!body) {
      if (!silent) {
        setIssues(["performedAt"]);
      }
      return;
    }
    const saved = await save.mutateAsync({
      examId,
      createBody: body.create,
      updateBody: body.update,
      silent,
    });
    const next = {
      ...draft,
      version: saved.version,
      procedureId: saved.procedureId,
      procedureStatus: saved.procedureStatus,
      removalDueDate: saved.procedure?.removalDueDate ?? null,
    };
    loadedKey.current = `${saved.publicId}:${saved.version}:${timeZone}`;
    setDraft(next);
    setBaseline(JSON.stringify(next));
    setIssues([]);
    if (saved.publicId !== examId) {
      onExamChange(saved.publicId);
    }
  }
  persistLatest.current = persist;

  if (exams.isLoading) {
    return (
      <p {...testIdProps(testIds.otology.loading)}>{t("state.loading")}</p>
    );
  }
  if (exams.isError) {
    return <p {...testIdProps(testIds.otology.error)}>{t("state.error")}</p>;
  }

  return (
    <div className="space-y-6" {...testIdProps(testIds.otology.root)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">{t("title")}</h2>
        <button
          type="button"
          className="rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
          onClick={() => {
            setDraft(emptyDraft(localNow()));
            setIssues([]);
            onExamChange(null);
          }}
          {...testIdProps(testIds.otology.newExam)}
        >
          {t("actions.new")}
        </button>
      </div>
      <div {...testIdProps(testIds.otology.list)}>
        {exams.data?.items.length ? (
          <ul className="flex flex-wrap gap-2">
            {exams.data.items.map((exam) => (
              <li key={exam.publicId}>
                <button
                  type="button"
                  className="rounded-full border border-border px-3 py-1 text-sm"
                  onClick={() => onExamChange(exam.publicId)}
                  {...testIdProps(otologyExamTestId(exam.publicId))}
                >
                  {methodLabel(t, exam.method)}
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p {...testIdProps(testIds.otology.empty)}>{t("state.empty")}</p>
        )}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Field
          label={t("fields.performedAt")}
          testId={testIds.otology.performedAt}
        >
          <input
            type="datetime-local"
            disabled={readOnly}
            value={draft.performedAt}
            onChange={(event) =>
              setDraft({ ...draft, performedAt: event.target.value })
            }
          />
        </Field>
        <SelectField
          label={t("fields.method")}
          testId={testIds.otology.method}
          value={draft.method}
          disabled={readOnly}
          onChange={(method) =>
            setDraft({ ...draft, method: method as OtologyDraft["method"] })
          }
          options={METHODS.map((value) => ({
            value,
            label: methodLabel(t, value),
          }))}
        />
        <SelectField
          label={t("fields.laterality")}
          testId={testIds.otology.laterality}
          value={draft.laterality}
          disabled={readOnly}
          onChange={(laterality) =>
            setDraft({
              ...draft,
              laterality: laterality as OtologyDraft["laterality"],
            })
          }
          options={LATERALITIES.map((value) => ({
            value,
            label: lateralityLabel(t, value),
          }))}
        />
        <SelectField
          label={t("fields.weber")}
          testId={testIds.otology.weber}
          value={draft.weber}
          disabled={readOnly}
          onChange={(weber) =>
            setDraft({ ...draft, weber: weber as OtologyDraft["weber"] })
          }
          options={["", ...WEBER].map((value) => ({
            value,
            label: optionLabel(t, "weber", value),
          }))}
        />
        <SelectField
          label={t("fields.rinneRight")}
          testId={testIds.otology.rinneRight}
          value={draft.rinneRight}
          disabled={readOnly}
          onChange={(rinneRight) =>
            setDraft({
              ...draft,
              rinneRight: rinneRight as OtologyDraft["rinneRight"],
            })
          }
          options={["", ...RINNE].map((value) => ({
            value,
            label: optionLabel(t, "rinne", value),
          }))}
        />
        <SelectField
          label={t("fields.rinneLeft")}
          testId={testIds.otology.rinneLeft}
          value={draft.rinneLeft}
          disabled={readOnly}
          onChange={(rinneLeft) =>
            setDraft({
              ...draft,
              rinneLeft: rinneLeft as OtologyDraft["rinneLeft"],
            })
          }
          options={["", ...RINNE].map((value) => ({
            value,
            label: optionLabel(t, "rinne", value),
          }))}
        />
        <SelectField
          label={t("fields.fork")}
          testId={testIds.otology.fork}
          value={draft.fork}
          disabled={readOnly}
          onChange={(fork) =>
            setDraft({ ...draft, fork: fork as OtologyDraft["fork"] })
          }
          options={["", ...FORKS].map((value) => ({
            value,
            label: optionLabel(t, "fork", value),
          }))}
        />
        <SelectField
          label={t("fields.mobilityRight")}
          testId={testIds.otology.mobilityRight}
          value={draft.mobilityRight}
          disabled={readOnly}
          onChange={(mobilityRight) =>
            setDraft({
              ...draft,
              mobilityRight: mobilityRight as OtologyDraft["mobilityRight"],
            })
          }
          options={["", ...MOBILITY].map((value) => ({
            value,
            label: optionLabel(t, "mobility", value),
          }))}
        />
        <SelectField
          label={t("fields.mobilityLeft")}
          testId={testIds.otology.mobilityLeft}
          value={draft.mobilityLeft}
          disabled={readOnly}
          onChange={(mobilityLeft) =>
            setDraft({
              ...draft,
              mobilityLeft: mobilityLeft as OtologyDraft["mobilityLeft"],
            })
          }
          options={["", ...MOBILITY].map((value) => ({
            value,
            label: optionLabel(t, "mobility", value),
          }))}
        />
      </div>
      <div {...testIdProps(testIds.otology.map)}>
        <AnatomicalMap
          definition={tympanicMembraneMap}
          selectedSide={side}
          marks={marksForSide(draft, side)}
          findingsByValueSet={findingsByValueSet}
          findingsLoading={membrane.isLoading || canal.isLoading}
          onSelectedSideChange={setSide}
          onMarkNormal={(region) =>
            setDraft((current) => applyMapNormal(current, region, side))
          }
          onSelectFinding={(region, code) =>
            setDraft((current) => applyMapFinding(current, region, side, code))
          }
          onMarkNotExamined={(region) =>
            setDraft((current) => applyMapNotExamined(current, region, side))
          }
        />
      </div>
      <OtologyProcedureForm
        draft={draft}
        devices={openTubeDevices(devices.data?.items ?? [])}
        readOnly={readOnly}
        onChange={setDraft}
      />
      <label className="block space-y-1 text-sm">
        {t("fields.conclusion")}
        <textarea
          className="min-h-24 w-full rounded-lg border border-input bg-card px-3 py-2 text-sm"
          disabled={readOnly}
          value={draft.conclusionText}
          onChange={(event) =>
            setDraft({ ...draft, conclusionText: event.target.value })
          }
          {...testIdProps(testIds.otology.conclusion)}
        />
      </label>
      {issues.length > 0 ? (
        <ul {...testIdProps(testIds.otology.validation)}>
          {issues.map((issue) => (
            <li key={issue}>{t(`validation.${issue}` as "validation.fork")}</li>
          ))}
        </ul>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          disabled={readOnly || save.isPending}
          onClick={() => void persist(false)}
          {...testIdProps(testIds.otology.save)}
        >
          {save.isPending ? t("actions.saving") : t("actions.save")}
        </button>
        <button
          type="button"
          className="rounded-full border border-border px-4 py-2 text-sm font-medium disabled:opacity-50"
          disabled={readOnly || !draft.procedureId || sign.isPending}
          onClick={() => setConfirmingSign(true)}
          {...testIdProps(testIds.otology.sign)}
        >
          {t("actions.sign")}
        </button>
      </div>
      {confirmingSign ? (
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground"
            onClick={() => {
              if (draft.procedureId) {
                void sign.mutateAsync(draft.procedureId).then(() => {
                  setDraft((current) => ({
                    ...current,
                    procedureStatus: "signed",
                  }));
                  setConfirmingSign(false);
                });
              }
            }}
            {...testIdProps(testIds.otology.confirmSign)}
          >
            {t("actions.confirmSign")}
          </button>
          <button
            type="button"
            className="rounded-full border border-border px-4 py-2 text-sm"
            onClick={() => setConfirmingSign(false)}
            {...testIdProps(testIds.otology.cancelSign)}
          >
            {t("actions.cancelSign")}
          </button>
        </div>
      ) : null}
      <DeviceList
        devices={devices.data?.items ?? []}
        disabled={updateDevice.isPending}
        onStatus={(device, status) =>
          updateDevice.mutate({
            deviceId: device.publicId,
            body: { version: device.version, status },
          })
        }
      />
    </div>
  );
}

function DeviceList({
  devices,
  disabled,
  onStatus,
}: {
  devices: readonly EarDeviceRead[];
  disabled: boolean;
  onStatus: (
    device: EarDeviceRead,
    status: (typeof DEVICE_STATUSES)[number],
  ) => void;
}) {
  const t = useTranslations("otology");
  return (
    <section className="space-y-2" {...testIdProps(testIds.otology.devices)}>
      <h3 className="text-sm font-semibold">{t("fields.devices")}</h3>
      {devices.length === 0 ? <p>{t("devicesEmpty")}</p> : null}
      <ul className="space-y-2">
        {devices.map((device) => (
          <li
            key={device.publicId}
            className="flex flex-wrap items-center gap-3"
          >
            <span>
              {optionLabel(t, "deviceType", device.deviceType)}{" "}
              {optionLabel(t, "laterality", device.laterality)}
            </span>
            <span>{t("nextCheck", { date: device.nextCheckDue })}</span>
            <select
              className="h-10 rounded-lg border border-input bg-card px-2 text-sm"
              disabled={disabled}
              value={device.status}
              onChange={(event) =>
                onStatus(
                  device,
                  event.target.value as (typeof DEVICE_STATUSES)[number],
                )
              }
              {...testIdProps(otologyDeviceStatusTestId(device.publicId))}
            >
              {DEVICE_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {optionLabel(t, "deviceStatus", status)}
                </option>
              ))}
            </select>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Field({
  label,
  testId,
  children,
}: {
  label: string;
  testId: string;
  children: ReactElement<InputHTMLAttributes<HTMLInputElement>>;
}) {
  return (
    <label className="space-y-1 text-sm">
      {label}
      {cloneElement(children, {
        className:
          "flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm",
        ...testIdProps(testId),
      })}
    </label>
  );
}

function SelectField({
  label,
  testId,
  value,
  disabled,
  options,
  onChange,
}: {
  label: string;
  testId: string;
  value: string;
  disabled: boolean;
  options: readonly { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="space-y-1 text-sm">
      {label}
      <select
        className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
        disabled={disabled}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        {...testIdProps(testId)}
      >
        {options.map((option) => (
          <option key={option.value || "none"} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function options(
  members: readonly { code: string; display: string }[],
): MapFindingOption[] {
  return members
    .filter((member) => !HIDDEN_FINDINGS.has(member.code))
    .map((member) => ({ code: member.code, display: member.display }));
}

function localNow(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  const hour = String(now.getHours()).padStart(2, "0");
  const minute = String(now.getMinutes()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}T${hour}:${minute}`;
}
