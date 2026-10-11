import { Suspense } from "react";

import { EndoscopyPage } from "@/features/endoscopy";

export default async function PatientEndoscopyPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  return (
    <Suspense fallback={null}>
      <EndoscopyPage patientId={patientId} />
    </Suspense>
  );
}
