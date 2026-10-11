"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { formControlClass } from "@/components/ui/form-control";
import { usePatientsQuery } from "@/features/patients";
import {
  useAppointmentTypesQuery,
  useSchedulableDoctorsQuery,
  useSchedulingSitesQuery,
} from "@/features/scheduling";
import type { RecallCreate, RecallRead } from "@/lib/api/generated";
import { formatPersonName } from "@/lib/i18n/format";
import { publicIdTestId, testIdProps, testIds } from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

import {
  useBookRecallMutation,
  useCreateRecallMutation,
} from "../hooks/use-recall-queries";
import {
  recallIntervalLabel,
  recallTestLabel,
  recallActionTypeLabel,
} from "../lib/labels";
import { timelineLateralityLabel } from "@/features/patients";

const INTERVALS = [7, 14, 28, 42, 90, 180, 365] as const;
const ACTION_TYPES = [
  "visit",
  "test",
  "call",
  "questionnaire",
  "document",
] as const;
const TESTS = ["audiogram", "tympanometry", "endoscopy", "imaging"] as const;
const SIDES = ["", "right", "left", "bilateral", "midline", "na"] as const;

export type RecallPreset = "follow_up" | "test_requested" | "manual";

type RecallComposerProps = {
  heading: string;
  preset?: RecallPreset;
  patientId?: string;
  encounterId?: string | null;
  initialReason?: string;
  recall?: RecallRead;
  onClose: () => void;
};

function appointmentTypeLabel(
  t: ReturnType<typeof useTranslations>,
  nameKey: string,
): string {
  const key = nameKey.startsWith("scheduling.")
    ? nameKey.slice("scheduling.".length)
    : nameKey;
  switch (key) {
    case "appointment_type.audiology_slot":
      return t("appointment_type.audiology_slot");
    case "appointment_type.follow_up":
      return t("appointment_type.follow_up");
    case "appointment_type.new_consultation":
      return t("appointment_type.new_consultation");
    case "appointment_type.post_op_check":
      return t("appointment_type.post_op_check");
    case "appointment_type.procedure":
      return t("appointment_type.procedure");
    case "appointment_type.surgery":
      return t("appointment_type.surgery");
    default:
      return t("appointment_type.follow_up");
  }
}

export function RecallComposer({
  heading,
  preset = "manual",
  patientId,
  encounterId,
  initialReason = "",
  recall,
  onClose,
}: RecallComposerProps) {
  const t = useTranslations("recalls");
  const tPatients = useTranslations("patients");
  const tScheduling = useTranslations("scheduling");
  const locale = useLocale();
  const booking = recall !== undefined;
  const create = useCreateRecallMutation();
  const book = useBookRecallMutation();
  const types = useAppointmentTypesQuery();
  const doctors = useSchedulableDoctorsQuery();
  const sites = useSchedulingSitesQuery();
  const [idempotencyKey] = useState(() => crypto.randomUUID());
  const [patientSearch, setPatientSearch] = useState("");
  const [selectedPatientId, setSelectedPatientId] = useState(
    patientId ?? recall?.patientId ?? "",
  );
  const [reason, setReason] = useState(
    initialReason || recall?.reasonText || "",
  );
  const [intervalDays, setIntervalDays] = useState(42);
  const [actionType, setActionType] = useState<
    "visit" | "test" | "call" | "questionnaire" | "document"
  >(preset === "test_requested" ? "test" : "visit");
  const [test, setTest] = useState<(typeof TESTS)[number]>("audiogram");
  const [laterality, setLaterality] = useState("");
  const [windowDays, setWindowDays] = useState(14);
  const [bookNow, setBookNow] = useState(booking);
  const [siteId, setSiteId] = useState("");
  const [userId, setUserId] = useState("");
  const [appointmentTypeId, setAppointmentTypeId] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [room, setRoom] = useState("");
  const [missing, setMissing] = useState(false);
  const patients = usePatientsQuery({
    search: patientSearch.trim() || undefined,
    limit: 8,
  });

  const appointment = () => {
    const start = new Date(startsAt);
    if (
      !siteId ||
      !userId ||
      !appointmentTypeId ||
      Number.isNaN(start.getTime())
    ) {
      return null;
    }
    return {
      siteId,
      userId,
      appointmentTypeId,
      startsAt: start.toISOString(),
      room: room.trim() || null,
    };
  };

  const submit = () => {
    const slot = bookNow || booking ? appointment() : null;
    if ((bookNow || booking) && !slot) {
      setMissing(true);
      return;
    }
    if (booking && recall) {
      if (!slot) {
        return;
      }
      book.mutate(
        {
          recallId: recall.publicId,
          body: { appointment: slot, version: recall.version },
        },
        { onSuccess: onClose },
      );
      return;
    }
    if (!selectedPatientId || reason.trim().length === 0) {
      setMissing(true);
      return;
    }
    const body: RecallCreate = {
      patientId: selectedPatientId,
      reasonText: reason.trim(),
      reasonLocale: locale,
      intervalDays,
      windowDays,
      actionType,
      actionConfig: actionType === "test" ? { test } : null,
      laterality:
        laterality === "right" ||
        laterality === "left" ||
        laterality === "bilateral" ||
        laterality === "midline" ||
        laterality === "na"
          ? laterality
          : null,
      sourceEncounterId: encounterId ?? null,
      appointment: slot,
    };
    create.mutate({ body, idempotencyKey }, { onSuccess: onClose });
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-foreground/40 p-4 sm:items-center"
      {...testIdProps(testIds.recalls.composer)}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={heading}
        className="max-h-[90vh] w-full max-w-xl space-y-4 overflow-y-auto rounded-xl bg-card p-5 shadow-lg"
      >
        <h2 className="text-lg font-semibold">{heading}</h2>
        {booking ? null : (
          <>
            {patientId ? null : (
              <div className="space-y-2">
                <Label>{t("form.patientSearch")}</Label>
                <Input
                  value={patientSearch}
                  onChange={(event) => setPatientSearch(event.target.value)}
                  {...testIdProps(testIds.recalls.patientSearch)}
                />
                <ul className="space-y-1">
                  {(patients.data?.items ?? []).map((patient) => (
                    <li key={patient.publicId}>
                      <Button
                        type="button"
                        variant={
                          selectedPatientId === patient.publicId
                            ? "secondary"
                            : "ghost"
                        }
                        onClick={() => setSelectedPatientId(patient.publicId)}
                        {...testIdProps(
                          publicIdTestId("recalls.patient", patient.publicId),
                        )}
                      >
                        {formatPersonName(
                          {
                            given: patient.firstName,
                            family: patient.lastName,
                          },
                          locale,
                        )}
                      </Button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div>
              <Label>{t("form.reason")}</Label>
              <Input
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                {...testIdProps(testIds.recalls.reason)}
              />
            </div>
            <div>
              <Label>{t("form.interval")}</Label>
              <Select
                className={cn(formControlClass, "w-full")}
                value={String(intervalDays)}
                onChange={(event) =>
                  setIntervalDays(Number(event.target.value))
                }
                {...testIdProps(testIds.recalls.interval)}
              >
                {INTERVALS.map((days) => (
                  <option key={days} value={days}>
                    {recallIntervalLabel(t, days)}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t("form.actionType")}</Label>
              <Select
                className={cn(formControlClass, "w-full")}
                value={actionType}
                onChange={(event) =>
                  setActionType(event.target.value as typeof actionType)
                }
                {...testIdProps(testIds.recalls.actionType)}
              >
                {ACTION_TYPES.map((kind) => (
                  <option key={kind} value={kind}>
                    {recallActionTypeLabel(t, kind)}
                  </option>
                ))}
              </Select>
            </div>
            {actionType === "test" ? (
              <div>
                <Label>{t("form.test")}</Label>
                <Select
                  className={cn(formControlClass, "w-full")}
                  value={test}
                  onChange={(event) =>
                    setTest(event.target.value as typeof test)
                  }
                  {...testIdProps(testIds.recalls.test)}
                >
                  {TESTS.map((kind) => (
                    <option key={kind} value={kind}>
                      {recallTestLabel(t, kind)}
                    </option>
                  ))}
                </Select>
              </div>
            ) : null}
            <div>
              <Label>{t("form.laterality")}</Label>
              <Select
                className={cn(formControlClass, "w-full")}
                value={laterality}
                onChange={(event) => setLaterality(event.target.value)}
                {...testIdProps(testIds.recalls.laterality)}
              >
                {SIDES.map((side) => (
                  <option key={side || "none"} value={side}>
                    {side === ""
                      ? t("form.none")
                      : timelineLateralityLabel(tPatients, side)}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t("form.window")}</Label>
              <Input
                type="number"
                min={0}
                max={180}
                value={windowDays}
                onChange={(event) => setWindowDays(Number(event.target.value))}
                {...testIdProps(testIds.recalls.window)}
              />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={bookNow}
                onChange={(event) => setBookNow(event.target.checked)}
                {...testIdProps(testIds.recalls.bookNow)}
              />
              {t("form.bookNow")}
            </label>
          </>
        )}
        {bookNow || booking ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label>{t("form.site")}</Label>
              <Select
                className={cn(formControlClass, "w-full")}
                value={siteId}
                onChange={(event) => setSiteId(event.target.value)}
                {...testIdProps(testIds.recalls.site)}
              >
                <option value="">{t("form.none")}</option>
                {(sites.data?.items ?? []).map((site) => (
                  <option key={site.publicId} value={site.publicId}>
                    {site.name}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t("form.doctor")}</Label>
              <Select
                className={cn(formControlClass, "w-full")}
                value={userId}
                onChange={(event) => setUserId(event.target.value)}
                {...testIdProps(testIds.recalls.doctor)}
              >
                <option value="">{t("form.none")}</option>
                {(doctors.data?.items ?? []).map((doctor) => (
                  <option key={doctor.publicId} value={doctor.publicId}>
                    {doctor.firstName} {doctor.lastName}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t("form.appointmentType")}</Label>
              <Select
                className={cn(formControlClass, "w-full")}
                value={appointmentTypeId}
                onChange={(event) => setAppointmentTypeId(event.target.value)}
                {...testIdProps(testIds.recalls.appointmentType)}
              >
                <option value="">{t("form.none")}</option>
                {(types.data?.items ?? []).map((type) => (
                  <option key={type.publicId} value={type.publicId}>
                    {appointmentTypeLabel(tScheduling, type.nameKey)}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t("form.startsAt")}</Label>
              <Input
                type="datetime-local"
                value={startsAt}
                onChange={(event) => setStartsAt(event.target.value)}
                {...testIdProps(testIds.recalls.startsAt)}
              />
            </div>
            <div>
              <Label>{t("form.room")}</Label>
              <Input
                value={room}
                onChange={(event) => setRoom(event.target.value)}
                {...testIdProps(testIds.recalls.room)}
              />
            </div>
          </div>
        ) : null}
        {missing ? (
          <p
            className="text-sm text-destructive"
            {...testIdProps(testIds.recalls.missing)}
          >
            {t("form.missing")}
          </p>
        ) : null}
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            {...testIdProps(testIds.recalls.close)}
          >
            {t("dialog.close")}
          </Button>
          <Button
            type="button"
            disabled={create.isPending || book.isPending}
            onClick={submit}
            {...testIdProps(testIds.recalls.submit)}
          >
            {booking ? t("dialog.bookSubmit") : t("dialog.createSubmit")}
          </Button>
        </div>
      </div>
    </div>
  );
}
