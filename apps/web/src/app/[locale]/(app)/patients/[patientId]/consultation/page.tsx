import { ConsultationCockpit } from "@/features/encounters";

export default async function PatientConsultationPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  return <ConsultationCockpit patientId={patientId} />;
}
