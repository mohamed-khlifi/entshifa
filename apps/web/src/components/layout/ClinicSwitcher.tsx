"use client";

import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";

import { useClinicMembershipsQuery } from "@/features/auth";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

export function ClinicSwitcher() {
  const t = useTranslations("common");
  const { session, switchClinic } = useSession();
  const { data, isLoading } = useClinicMembershipsQuery();
  const [busy, setBusy] = useState(false);

  const items = useMemo(() => data?.items ?? [], [data?.items]);
  const visible = items.length > 1;

  const options = useMemo(
    () =>
      items.map((item) => ({
        value: item.clinicPublicId,
        label: item.clinicName,
      })),
    [items],
  );

  if (!visible || !session) {
    return null;
  }

  return (
    <div
      className="hidden min-w-0 sm:block"
      {...testIdProps(testIds.layout.clinicSwitcher)}
    >
      <label className="sr-only" htmlFor="clinic-switcher">
        {t("clinicSwitcher.label")}
      </label>
      <select
        id="clinic-switcher"
        className="h-9 max-w-[12rem] truncate rounded-md border border-input bg-background px-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        disabled={isLoading || busy}
        value={session.clinicPublicId}
        onChange={(event) => {
          const next = event.target.value;
          if (next === session.clinicPublicId) {
            return;
          }
          setBusy(true);
          void switchClinic(next).finally(() => setBusy(false));
        }}
        {...testIdProps(testIds.layout.clinicSwitcherSelect)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
