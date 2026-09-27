import { Suspense } from "react";

import { AttachmentGallery } from "@/features/attachments";

export default async function PatientAttachmentsPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  return (
    <Suspense fallback={null}>
      <AttachmentGallery patientPublicId={patientId} />
    </Suspense>
  );
}
