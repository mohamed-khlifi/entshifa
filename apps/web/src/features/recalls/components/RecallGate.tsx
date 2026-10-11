"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { Permission } from "@/lib/permissions";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { Can } from "@/providers/permission-provider";

export function RecallGate({ children }: { children: ReactNode }) {
  const t = useTranslations("recalls");

  return (
    <Can
      permission={Permission.RECALL_READ}
      fallback={
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.recalls.gate)}
        >
          {t("gate.forbidden")}
        </p>
      }
    >
      {children}
    </Can>
  );
}
