import { Suspense } from "react";

import { LaryngoscopyPage } from "@/features/laryngoscopy";

export default async function PatientLaryngoscopyPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  return (
    <Suspense fallback={null}>
      <LaryngoscopyPage patientId={patientId} />
    </Suspense>
  );
}
