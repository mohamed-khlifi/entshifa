import { Suspense } from "react";

import { OtologyPage } from "@/features/otology";

export default async function PatientOtologyPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  return (
    <Suspense fallback={null}>
      <OtologyPage patientId={patientId} />
    </Suspense>
  );
}
