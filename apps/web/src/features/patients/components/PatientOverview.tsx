"use client";

import { PatientChart } from "../components/PatientChart";
import { PatientEditForm } from "../components/PatientEditForm";
import { usePatientQuery } from "../hooks/use-patient-queries";

export function PatientOverview({ patientId }: { patientId: string }) {
  const patient = usePatientQuery(patientId);
  if (!patient.data) {
    return null;
  }
  return (
    <div className="space-y-10">
      <PatientEditForm patient={patient.data} />
      <PatientChart patient={patient.data} />
    </div>
  );
}
