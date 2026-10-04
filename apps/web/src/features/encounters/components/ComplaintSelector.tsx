"use client";

import { useTranslations } from "next-intl";
import { useWatch } from "react-hook-form";

import { TextField } from "@/components/forms/TextField";
import {
  encounterComplaintTestId,
  encounterMakePrimaryTestId,
  encounterRegionTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

import type { CockpitFormValues } from "../schemas/cockpit.schema";
import {
  groupComplaints,
  type ComplaintChoice,
  type SelectedComplaint,
} from "../lib/complaints";
import { complaintRegionLabel } from "../lib/labels";

type ComplaintSelectorProps = {
  members: readonly ComplaintChoice[];
  selected: readonly SelectedComplaint[];
  disabled: boolean;
  onToggle: (choice: ComplaintChoice) => void;
  onMakePrimary: (code: string) => void;
};

export function ComplaintSelector({
  members,
  selected,
  disabled,
  onToggle,
  onMakePrimary,
}: ComplaintSelectorProps) {
  const t = useTranslations("encounters");
  const watched = useWatch<CockpitFormValues>({ name: "complaintSearch" });
  const search = typeof watched === "string" ? watched : "";
  const groups = groupComplaints(members, search);
  const selectedCodes = new Set(selected.map((item) => item.code));

  return (
    <section
      className="space-y-3"
      {...testIdProps(testIds.encounters.complaints)}
    >
      <h2 className="text-lg font-semibold">{t("complaints.title")}</h2>
      <TextField
        name="complaintSearch"
        label={t("complaints.search")}
        type="search"
        disabled={disabled}
      />
      {groups.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("complaints.empty")}</p>
      ) : (
        groups.map((group) => (
          <div key={group.region} className="space-y-2">
            <h3
              className="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
              {...testIdProps(encounterRegionTestId(group.region))}
            >
              {complaintRegionLabel(t, group.region)}
            </h3>
            <div className="flex flex-wrap gap-2">
              {group.items.map((item) => {
                const active = selected.find((row) => row.code === item.code);
                return (
                  <div key={item.code} className="flex items-center gap-1">
                    <button
                      type="button"
                      disabled={disabled}
                      aria-pressed={selectedCodes.has(item.code)}
                      className={
                        active
                          ? "rounded-full bg-primary px-3 py-1.5 text-sm text-primary-foreground"
                          : "rounded-full border border-border bg-card px-3 py-1.5 text-sm"
                      }
                      onClick={() => onToggle(item)}
                      {...testIdProps(encounterComplaintTestId(item.code))}
                    >
                      {item.display}
                      {active?.isPrimary ? (
                        <span className="ms-1 text-xs">
                          {t("complaints.primary")}
                        </span>
                      ) : null}
                    </button>
                    {active && !active.isPrimary ? (
                      <button
                        type="button"
                        disabled={disabled}
                        className="text-xs text-primary underline-offset-2 hover:underline"
                        onClick={() => onMakePrimary(item.code)}
                        {...testIdProps(encounterMakePrimaryTestId(item.code))}
                      >
                        {t("complaints.makePrimary")}
                      </button>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </div>
        ))
      )}
    </section>
  );
}
