"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { Permission } from "@/lib/permissions";
import { Can } from "@/providers/permission-provider";

export function TerminologyAdminGate({ children }: { children: ReactNode }) {
  const t = useTranslations("errors");
  return (
    <Can
      permission={Permission.ADMIN_TERMINOLOGY}
      fallback={<p className="text-sm text-muted-foreground">{t("forbidden")}</p>}
    >
      {children}
    </Can>
  );
}
