import { Suspense } from "react";

import { AudiologyPage } from "@/features/audiology";

export default async function PatientAudiologyPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  return (
    <Suspense fallback={null}>
      <AudiologyPage patientId={patientId} />
    </Suspense>
  );
}
