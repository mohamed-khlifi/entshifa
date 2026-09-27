import { DocumentsGate, PatientDocumentsPanel } from "@/features/documents";

export default async function PatientDocumentsPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  return (
    <DocumentsGate>
      <PatientDocumentsPanel patientPublicId={patientId} />
    </DocumentsGate>
  );
}
