import { PatientTimeline } from "@/features/patients";

export default async function PatientTimelinePage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  return <PatientTimeline patientId={patientId} />;
}
