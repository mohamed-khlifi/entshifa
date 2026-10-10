"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { Permission } from "@/lib/permissions";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { Can } from "@/providers/permission-provider";

export function PrescriptionsGate({ children }: { children: ReactNode }) {
  const t = useTranslations("prescriptions");
  return (
    <Can
      permission={Permission.PRESCRIPTION_CREATE}
      fallback={
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.prescriptions.gate)}
        >
          {t("gate.forbidden")}
        </p>
      }
    >
      {children}
    </Can>
  );
}
