"use client";

import { useSearchParams } from "next/navigation";

import { OfficeProcedureWorkspace } from "./OfficeProcedureWorkspace";
import { usePathname, useRouter } from "@/lib/i18n/navigation";

export function OfficeProceduresPage({ patientId }: { patientId: string }) {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const procedureId = params.get("procedure");
  return (
    <OfficeProcedureWorkspace
      patientId={patientId}
      procedureId={procedureId}
      onProcedureChange={(next) => {
        const query = next ? `?procedure=${next}` : "";
        router.replace(`${pathname}${query}`);
      }}
    />
  );
}
