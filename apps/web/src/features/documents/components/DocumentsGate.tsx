"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { Permission } from "@/lib/permissions";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { Can } from "@/providers/permission-provider";

export function DocumentsGate({
  children,
  admin = false,
}: {
  children: ReactNode;
  admin?: boolean;
}) {
  const t = useTranslations("documents");
  const permission = admin
    ? Permission.ADMIN_TEMPLATES
    : Permission.DOCUMENT_FINALIZE;

  return (
    <Can
      permission={permission}
      fallback={
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.documents.gate)}
        >
          {t("gate.forbidden")}
        </p>
      }
    >
      {children}
    </Can>
  );
}
