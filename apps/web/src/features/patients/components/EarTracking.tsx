"use client";

import { useTranslations } from "next-intl";

import { activeFlags } from "../lib/active-flags";
import { flagLabel } from "../lib/labels";
import type { PatientFlagRead } from "@/lib/api/generated";
import { patientEarFlagTestId, testIdProps, testIds } from "@/lib/test/test-id";

const EAR_FLAGS = new Set([
  "ventilation_tube",
  "mastoid_cavity",
  "cholesteatoma",
]);

type EarTrackingProps = {
  flags: readonly PatientFlagRead[];
};

export function EarTracking({ flags }: EarTrackingProps) {
  const t = useTranslations("patients");
  const tForms = useTranslations("forms");
  const rows = activeFlags(flags).filter((flag) =>
    EAR_FLAGS.has(flag.flagCode),
  );

  return (
    <div
      className="mt-3 rounded-lg bg-muted/50 px-3 py-2"
      {...testIdProps(testIds.patients.headerEars)}
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {t("header.earTracking")}
      </p>
      {rows.length === 0 ? (
        <p className="mt-1 text-sm text-muted-foreground">
          {t("header.earTrackingEmpty")}
        </p>
      ) : (
        <ul className="mt-2 flex flex-wrap gap-2">
          {rows.map((flag) => (
            <li
              key={flag.publicId}
              className="rounded-full border border-border bg-card px-3 py-1 text-sm"
              {...testIdProps(
                patientEarFlagTestId(flag.flagCode, flag.laterality ?? ""),
              )}
            >
              {flagLabel(t, flag.flagCode)}
              {flag.laterality
                ? ` · ${sideLabel(tForms, flag.laterality)}`
                : ""}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function sideLabel(
  t: ReturnType<typeof useTranslations<"forms">>,
  value: string,
): string {
  switch (value) {
    case "left":
      return t("laterality.left");
    case "right":
      return t("laterality.right");
    case "bilateral":
      return t("laterality.bilateral");
    default:
      return value;
  }
}
