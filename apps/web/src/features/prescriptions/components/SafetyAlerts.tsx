"use client";

import { useTranslations } from "next-intl";

import {
  prescriptionAlertTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

import { alertCopy } from "../lib/labels";
import type { PlacedAlert } from "../lib/safety";

type SafetyAlertsProps = {
  alerts: readonly PlacedAlert[];
  blocked: boolean;
};

export function SafetyAlerts({ alerts, blocked }: SafetyAlertsProps) {
  const t = useTranslations("prescriptions");
  if (alerts.length === 0 && !blocked) {
    return null;
  }

  return (
    <section
      className="space-y-2 rounded-xl border border-destructive/40 bg-destructive/5 p-4"
      role="alert"
      {...testIdProps(testIds.prescriptions.safety)}
    >
      <h3 className="text-sm font-semibold">{t("safety.title")}</h3>
      {blocked ? (
        <p
          className="text-sm text-destructive"
          {...testIdProps(testIds.prescriptions.blocked)}
        >
          {t("builder.blocked")}
        </p>
      ) : null}
      <ul className="space-y-1">
        {alerts.map((alert) => (
          <li
            key={`${alert.code}-${alert.itemIndex ?? "all"}`}
            className="text-sm"
            {...testIdProps(prescriptionAlertTestId(alert.code))}
          >
            {alertCopy(t, alert)}
          </li>
        ))}
      </ul>
    </section>
  );
}
