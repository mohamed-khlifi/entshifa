"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { Permission } from "@/lib/permissions";
import { Can } from "@/providers/permission-provider";

export function UsersAdminGate({ children }: { children: ReactNode }) {
  const t = useTranslations("errors");

  return (
    <Can
      permission={Permission.ADMIN_USERS}
      fallback={
        <p className="text-sm text-muted-foreground">{t("forbidden")}</p>
      }
    >
      {children}
    </Can>
  );
}
