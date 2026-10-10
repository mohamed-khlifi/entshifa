"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { useCurrentClinicQuery } from "@/features/clinics";
import { usePatientQuery } from "@/features/patients";
import type { PrescriptionRead } from "@/lib/api/generated";
import {
  prescriptionRowTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

import { PrescriptionBuilder } from "./PrescriptionBuilder";
import { PrescriptionPaper } from "./PrescriptionPaper";
import {
  usePatientEncountersQuery,
  usePatientPrescriptionsQuery,
} from "../hooks/use-prescription-queries";
import { statusLabel } from "../lib/labels";
import { paperLocale } from "../lib/display";
import { paperShell, taperFromRecord, type PaperLine } from "../lib/paper";

function linesFromRecord(prescription: PrescriptionRead): PaperLine[] {
  return prescription.items.map((item) => ({
    title: item.concept?.display ?? item.drugInn ?? item.freeTextName ?? "",
    dose: item.doseAmount,
    unit: item.doseUnit,
    route: item.route,
    frequencyPerDay: item.frequencyPerDay,
    durationDays: item.durationDays,
    instructions: item.instructionsText,
    renewable: item.isRenewable,
    substitutionAllowed: item.substitutionAllowed,
    taper: taperFromRecord(item.taperSchedule),
  }));
}

export function PatientPrescriptionsPanel({
  patientPublicId,
}: {
  patientPublicId: string;
}) {
  const t = useTranslations("prescriptions");
  const patient = usePatientQuery(patientPublicId);
  const clinic = useCurrentClinicQuery();
  const prescriptions = usePatientPrescriptionsQuery(patientPublicId);
  const encounters = usePatientEncountersQuery(patientPublicId);
  const [encounterId, setEncounterId] = useState("");
  const [printing, setPrinting] = useState<PrescriptionRead | null>(null);

  const drafts = (encounters.data?.items ?? []).filter(
    (encounter) => encounter.status === "draft",
  );
  const chosen =
    drafts.find((encounter) => encounter.publicId === encounterId) ??
    drafts[0] ??
    null;
  const locale = paperLocale(
    patient.data?.preferredLocale,
    clinic.data?.defaultLocale,
  );
  const printed =
    printing && patient.data && clinic.data
      ? paperShell(
          clinic.data,
          patient.data,
          locale,
          printing.weightKg,
          printing.publicId,
          linesFromRecord(printing),
        )
      : null;

  if (prescriptions.isLoading || encounters.isLoading) {
    return (
      <p
        className="text-sm text-muted-foreground"
        {...testIdProps(testIds.prescriptions.loading)}
      >
        {t("page.loading")}
      </p>
    );
  }

  if (prescriptions.isError || encounters.isError) {
    return (
      <p
        className="text-sm text-destructive"
        {...testIdProps(testIds.prescriptions.error)}
      >
        {t("page.error")}
      </p>
    );
  }

  const rows = prescriptions.data?.items ?? [];

  return (
    <div className="space-y-6" {...testIdProps(testIds.prescriptions.root)}>
      <div className="space-y-1 print:hidden">
        <h1 className="text-2xl font-semibold">{t("page.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("page.description")}</p>
      </div>
      {rows.length === 0 ? (
        <p
          className="text-sm text-muted-foreground print:hidden"
          {...testIdProps(testIds.prescriptions.empty)}
        >
          {t("page.empty")}
        </p>
      ) : (
        <ul
          className="space-y-2 print:hidden"
          {...testIdProps(testIds.prescriptions.list)}
        >
          {rows.map((row) => (
            <li
              key={row.publicId}
              className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border px-4 py-3"
              {...testIdProps(prescriptionRowTestId(row.publicId))}
            >
              <div>
                <p className="text-sm font-medium">
                  {statusLabel(t, row.status)}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t("list.count", { count: row.items.length })}
                </p>
              </div>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setPrinting(row);
                  window.setTimeout(() => window.print(), 0);
                }}
              >
                {t("list.print")}
              </Button>
            </li>
          ))}
        </ul>
      )}
      {chosen ? (
        <div className="space-y-3 print:hidden">
          <label
            className="block text-sm"
            {...testIdProps(testIds.prescriptions.encounter)}
          >
            {t("encounter.label")}
            <select
              className="mt-1 flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
              value={chosen.publicId}
              onChange={(event) => setEncounterId(event.target.value)}
            >
              {drafts.map((encounter) => (
                <option key={encounter.publicId} value={encounter.publicId}>
                  {encounter.startedAt}
                </option>
              ))}
            </select>
          </label>
          <PrescriptionBuilder
            patientId={patientPublicId}
            encounterId={chosen.publicId}
            complaintConceptIds={chosen.complaints.map(
              (complaint) => complaint.concept.conceptId,
            )}
            showPaper={printing == null}
          />
        </div>
      ) : (
        <p
          className="text-sm text-muted-foreground print:hidden"
          {...testIdProps(testIds.prescriptions.needsEncounter)}
        >
          {t("encounter.empty")}
        </p>
      )}
      {printed ? <PrescriptionPaper locale={locale} model={printed} /> : null}
    </div>
  );
}
