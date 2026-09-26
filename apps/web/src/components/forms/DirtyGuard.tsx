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
    const onClickCapture = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }
      const anchor = target.closest("a");
      if (!anchor || anchor.target === "_blank") {
        return;
      }
      const href = anchor.getAttribute("href");
      if (!href || href.startsWith("#")) {
        return;
      }
      if (!window.confirm(t("dirtyGuard.message"))) {
        event.preventDefault();
        event.stopPropagation();
      }
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    document.addEventListener("click", onClickCapture, true);
    return () => {
      window.removeEventListener("beforeunload", onBeforeUnload);
      document.removeEventListener("click", onClickCapture, true);
    };
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
