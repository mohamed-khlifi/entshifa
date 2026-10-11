"use client";

import { useSearchParams } from "next/navigation";

import { EndoscopyWorkspace } from "./EndoscopyWorkspace";
import { usePathname, useRouter } from "@/lib/i18n/navigation";

export function EndoscopyPage({ patientId }: { patientId: string }) {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const examId = params.get("exam");
  return (
    <EndoscopyWorkspace
      patientId={patientId}
      examId={examId}
      onExamChange={(next) => {
        const query = next ? `?exam=${next}` : "";
        router.replace(`${pathname}${query}`);
      }}
    />
  );
}
