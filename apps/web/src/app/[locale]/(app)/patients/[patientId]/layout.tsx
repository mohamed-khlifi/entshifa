import type { ReactNode } from "react";

import { PatientShell, PatientsGate } from "@/features/patients";

export default async function PatientLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;

  return (
    <PatientsGate>
      <PatientShell patientId={patientId}>{children}</PatientShell>
    </PatientsGate>
  );
}
