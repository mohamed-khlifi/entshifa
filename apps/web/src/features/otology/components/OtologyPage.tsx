"use client";

import { useSearchParams } from "next/navigation";

import { OtologyWorkspace } from "./OtologyWorkspace";
import { usePathname, useRouter } from "@/lib/i18n/navigation";

export function OtologyPage({ patientId }: { patientId: string }) {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const examId = params.get("exam");
  return (
    <OtologyWorkspace
      patientId={patientId}
      examId={examId}
      onExamChange={(next) => {
        const query = next ? `?exam=${next}` : "";
        router.replace(`${pathname}${query}`);
      }}
    />
  );
}
