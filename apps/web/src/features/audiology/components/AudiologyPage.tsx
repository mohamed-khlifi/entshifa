"use client";

import { useSearchParams } from "next/navigation";

import { AudiogramWorkspace } from "./AudiogramWorkspace";
import { usePathname, useRouter } from "@/lib/i18n/navigation";

export function AudiologyPage({ patientId }: { patientId: string }) {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const audiogramId = params.get("audiogram");
  return (
    <AudiogramWorkspace
      patientId={patientId}
      audiogramId={audiogramId}
      onAudiogramChange={(next) => {
        const query = next ? `?audiogram=${next}` : "";
        router.replace(`${pathname}${query}`);
      }}
    />
  );
}
