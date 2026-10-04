import { ConsultationCockpit } from "@/features/encounters";

export default async function PatientEncounterPage({
  params,
}: {
  params: Promise<{ patientId: string; encounterId: string }>;
}) {
  const { patientId, encounterId } = await params;
  return (
    <ConsultationCockpit patientId={patientId} encounterId={encounterId} />
  );
}
