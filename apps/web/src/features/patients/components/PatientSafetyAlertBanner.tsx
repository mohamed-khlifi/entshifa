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

  return (
    <div className="space-y-3">
      {onlyHearingEar.length > 0 ? (
        <div
          role="alert"
          className="rounded-xl border-2 border-destructive bg-destructive px-4 py-4 text-destructive-foreground shadow-sm"
          {...testIdProps(testIds.patients.alertOnlyHearingEar)}
        >
          <p className="text-lg font-bold tracking-wide">
            {t("alerts.onlyHearingEar")}
          </p>
        </div>
      ) : null}
      {other.length > 0 ? (
        <div
          role="status"
          className="rounded-xl border border-amber-600/40 bg-amber-50 px-4 py-3 text-amber-950"
          {...testIdProps(testIds.patients.alertOther)}
        >
          <p className="text-sm font-semibold">{t("alerts.otherTitle")}</p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {other.map((flag) => (
              <li
                key={flag.publicId}
                className="rounded-full bg-amber-200 px-3 py-1 text-sm font-medium"
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
