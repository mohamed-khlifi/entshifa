"use client";

import { useSearchParams } from "next/navigation";

import { LaryngoscopyWorkspace } from "./LaryngoscopyWorkspace";
import { usePathname, useRouter } from "@/lib/i18n/navigation";

export function LaryngoscopyPage({ patientId }: { patientId: string }) {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const examId = params.get("exam");
  return (
    <LaryngoscopyWorkspace
      patientId={patientId}
      examId={examId}
      onExamChange={(next) => {
        const query = next ? `?exam=${next}` : "";
        router.replace(`${pathname}${query}`);
      }}
    />
  );
}
