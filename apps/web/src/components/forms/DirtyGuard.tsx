"use client";

import { useTranslations } from "next-intl";
import { useEffect, type ReactNode } from "react";
import { useFormContext } from "react-hook-form";

import { testIdProps, testIds } from "@/lib/test/test-id";

export type DirtyGuardProps = {
  /** When true, blocks browser unload if the form is dirty. */
  enabled?: boolean;
  children?: ReactNode;
};

/**
 * Warns before leaving with unsaved changes (beforeunload).
 * Route-level navigation blocking can wrap this when a router blocker is available.
 */
export function DirtyGuard({ enabled = true, children }: DirtyGuardProps) {
  const { formState } = useFormContext();
  const t = useTranslations("forms");
  const isDirty = formState.isDirty;

  useEffect(() => {
    if (!enabled || !isDirty) {
      return;
    }
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = t("dirtyGuard.message");
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [enabled, isDirty, t]);

  return (
    <div
      {...testIdProps(testIds.forms.dirtyGuard)}
      data-dirty={isDirty ? "true" : "false"}
    >
      {children}
    </div>
  );
}
