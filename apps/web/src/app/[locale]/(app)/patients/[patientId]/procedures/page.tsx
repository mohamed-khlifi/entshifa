import { Suspense } from "react";

import { OfficeProceduresPage } from "@/features/office-procedures";

export default async function PatientOfficeProceduresPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  return (
    <Suspense fallback={null}>
      <OfficeProceduresPage patientId={patientId} />
    </Suspense>
  );
}
