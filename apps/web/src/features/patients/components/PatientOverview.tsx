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
    <div className="space-y-8">
      <section className="rounded-xl border border-border bg-card p-6 shadow-[var(--shadow-soft)]">
        <PatientEditForm patient={patient.data} />
      </section>
      <section>
        <PatientChart patient={patient.data} />
      </section>
    </div>
  );
}
