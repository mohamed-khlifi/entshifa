"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { PatientHeaderCard } from "../components/PatientHeaderCard";
import { PatientSafetyAlertBanner } from "../components/PatientSafetyAlertBanner";
import {
  usePatientQuery,
  usePatientTimelineQuery,
} from "../hooks/use-patient-queries";
import { testIdProps, testIds } from "@/lib/test/test-id";

export function PatientShell({
  patientId,
  children,
}: {
  patientId: string;
  children: ReactNode;
}) {
  const t = useTranslations("patients");
  const patient = usePatientQuery(patientId);
  usePatientTimelineQuery(patientId);

  if (patient.isLoading) {
    return (
      <p
        className="text-sm text-muted-foreground"
        {...testIdProps(testIds.patients.loading)}
      >
        {t("state.loading")}
      </p>
    );
  }

  if (patient.isError || !patient.data) {
    return (
      <p
        className="text-sm text-destructive"
        {...testIdProps(testIds.patients.error)}
      >
        {t("state.loadError")}
      </p>
    );
  }

  return (
    <div className="space-y-6" {...testIdProps(testIds.patients.shell)}>
      <PatientSafetyAlertBanner flags={patient.data.flags} />
      <PatientHeaderCard patient={patient.data} />
      {children}
    </div>
  );
}
