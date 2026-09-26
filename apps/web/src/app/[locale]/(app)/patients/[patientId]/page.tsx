import { PatientOverview } from "@/features/patients";

export default async function PatientOverviewPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  return <PatientOverview patientId={patientId} />;
}
