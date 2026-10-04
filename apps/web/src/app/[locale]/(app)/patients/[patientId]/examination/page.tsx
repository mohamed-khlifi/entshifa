import { ExaminationWorkspace } from "@/features/examination";

export default async function PatientExaminationPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  return <ExaminationWorkspace patientId={patientId} />;
}
