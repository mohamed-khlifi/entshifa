"use client";

import { CloudOff, Loader2, Save, TriangleAlert } from "lucide-react";
import { useTranslations } from "next-intl";

import type { AutosaveStatus } from "@/lib/forms/autosave";
import { cn } from "@/lib/utils/cn";
import { testIdProps, testIds } from "@/lib/test/test-id";

export type AutosaveIndicatorProps = {
  status: AutosaveStatus;
  className?: string;
};

export function AutosaveIndicator({
  status,
  className,
}: AutosaveIndicatorProps) {
  const t = useTranslations("forms");

  const content = (() => {
    switch (status) {
      case "idle":
        return null;
      case "saving":
        return (
          <>
            <Loader2 className="size-3.5 animate-spin" aria-hidden />
            {t("autosave.saving")}
          </>
        );
      case "saved":
        return (
          <>
            <Save className="size-3.5" aria-hidden />
            {t("autosave.saved")}
          </>
        );
      case "offline":
        return (
          <>
            <CloudOff className="size-3.5" aria-hidden />
            {t("autosave.offline")}
          </>
        );
      case "conflict":
        return (
          <>
            <TriangleAlert className="size-3.5" aria-hidden />
            {t("autosave.conflict")}
          </>
        );
      case "error":
        return (
          <>
            <TriangleAlert className="size-3.5" aria-hidden />
            {t("autosave.error")}
          </>
        );
      default: {
        const _exhaustive: never = status;
        return _exhaustive;
      }
    }
  })();

  if (content === null) {
    return null;
  }

  return (
    <p
      className={cn(
        "inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground",
        status === "conflict" || status === "error" ? "text-destructive" : null,
        className,
      )}
      role="status"
      aria-live="polite"
      {...testIdProps(testIds.forms.autosave)}
    >
      {content}
    </p>
  );
}
