"use client";

import { useTranslations } from "next-intl";

import {
  encounterRedFlagTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

import { redFlagLabel } from "../lib/labels";
import {
  RED_FLAG_IDS,
  suggestedRedFlags,
  type RedFlagId,
} from "../lib/red-flags";

type RedFlagListProps = {
  complaintCodes: readonly string[];
  confirmed: readonly RedFlagId[];
  disabled: boolean;
  onToggle: (flag: RedFlagId) => void;
};

export function RedFlagList({
  complaintCodes,
  confirmed,
  disabled,
  onToggle,
}: RedFlagListProps) {
  const t = useTranslations("encounters");
  const suggested = new Set(suggestedRedFlags(complaintCodes));

  return (
    <section
      className="space-y-3"
      {...testIdProps(testIds.encounters.redFlags)}
    >
      <h2 className="text-lg font-semibold">{t("redFlags.title")}</h2>
      <p className="text-sm text-muted-foreground">{t("redFlags.hint")}</p>
      <ul className="space-y-2">
        {RED_FLAG_IDS.map((flag) => {
          const pressed = confirmed.includes(flag);
          return (
            <li key={flag}>
              <button
                type="button"
                disabled={disabled}
                aria-pressed={pressed}
                className={
                  pressed
                    ? "w-full rounded-lg border border-destructive bg-destructive/10 px-3 py-2 text-start text-sm"
                    : "w-full rounded-lg border border-border bg-card px-3 py-2 text-start text-sm"
                }
                onClick={() => onToggle(flag)}
                {...testIdProps(encounterRedFlagTestId(flag))}
              >
                <span className="font-medium">{redFlagLabel(t, flag)}</span>
                {suggested.has(flag) ? (
                  <span className="mt-1 block text-xs text-destructive">
                    {t("redFlags.suggested")}
                  </span>
                ) : null}
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
