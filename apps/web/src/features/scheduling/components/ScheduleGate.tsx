"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { Permission } from "@/lib/permissions";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { Can } from "@/providers/permission-provider";

export function ScheduleGate({ children }: { children: ReactNode }) {
  const t = useTranslations("scheduling");

  return (
    <Can
      permission={Permission.APPOINTMENT_READ}
      fallback={
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.scheduling.gate)}
        >
          {t("gate.forbidden")}
        </p>
      }
    >
      {children}
    </Can>
  );
}
