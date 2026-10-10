import {
  PatientPrescriptionsPanel,
  PrescriptionsGate,
} from "@/features/prescriptions";

export default async function PatientPrescriptionsPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  return (
    <PrescriptionsGate>
      <PatientPrescriptionsPanel patientPublicId={patientId} />
    </PrescriptionsGate>
  );
}
