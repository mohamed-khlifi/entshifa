"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { Permission } from "@/lib/permissions";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { Can } from "@/providers/permission-provider";

export function PatientsGate({ children }: { children: ReactNode }) {
  const t = useTranslations("patients");

  return (
    <Can
      permission={Permission.PATIENT_READ_CLINIC}
      fallback={
        <Can
          permission={Permission.PATIENT_READ_OWN}
          fallback={
            <p
              className="text-sm text-muted-foreground"
              {...testIdProps(testIds.patients.gate)}
            >
              {t("gate.forbidden")}
            </p>
          }
        >
          {children}
        </Can>
      }
    >
      {children}
    </Can>
  );
}
