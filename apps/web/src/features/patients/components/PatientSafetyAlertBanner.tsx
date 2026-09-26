"use client";

import { useTranslations } from "next-intl";

import { splitHearingAlerts } from "../lib/active-flags";
import { flagLabel } from "../lib/labels";
import type { PatientFlagRead } from "@/lib/api/generated";
import { testIdProps, testIds } from "@/lib/test/test-id";

type PatientSafetyAlertBannerProps = {
  flags: readonly PatientFlagRead[];
};

export function PatientSafetyAlertBanner({
  flags,
}: PatientSafetyAlertBannerProps) {
  const t = useTranslations("patients");
  const { onlyHearingEar, other } = splitHearingAlerts(flags);

  if (onlyHearingEar.length === 0 && other.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border bg-card px-4 py-3 shadow-[var(--shadow-soft)]">
      {onlyHearingEar.length > 0 ? (
        <p
          role="alert"
          className="inline-flex items-center gap-2 rounded-full border border-destructive/30 bg-destructive/10 px-3 py-1 text-sm font-semibold text-destructive"
          {...testIdProps(testIds.patients.alertOnlyHearingEar)}
        >
          <span className="h-2 w-2 shrink-0 rounded-full bg-destructive" />
          {t("alerts.onlyHearingEar")}
        </p>
      ) : null}
      {other.length > 0 ? (
        <div
          role="status"
          className="flex min-w-0 flex-wrap items-center gap-2"
          {...testIdProps(testIds.patients.alertOther)}
        >
          {onlyHearingEar.length === 0 ? (
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {t("alerts.otherTitle")}
            </p>
          ) : null}
          <ul className="flex flex-wrap gap-2">
            {other.map((flag) => (
              <li
                key={flag.publicId}
                className="rounded-full border border-border bg-muted px-3 py-1 text-sm text-foreground"
              >
                {flagLabel(t, flag.flagCode)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
