"use client";

import { useTranslations } from "next-intl";
import { useFormContext } from "react-hook-form";

import { SelectField } from "@/components/forms/SelectField";
import { TextAreaField } from "@/components/forms/TextAreaField";
import { TextField } from "@/components/forms/TextField";
import { Button } from "@/components/ui/button";
import { testIdProps, testIds } from "@/lib/test/test-id";

import { planKindLabel } from "../lib/labels";
import {
  PLAN_KINDS,
  type PlanItemDraft,
  type PlanKind,
} from "../lib/plan-items";
import type { CockpitFormValues } from "../schemas/cockpit.schema";

type PlanPanelProps = {
  items: readonly PlanItemDraft[];
  disabled: boolean;
  onAdd: (kind: PlanKind, detail: string) => void;
  onRemove: (id: string) => void;
};

export function PlanPanel({
  items,
  disabled,
  onAdd,
  onRemove,
}: PlanPanelProps) {
  const t = useTranslations("encounters");
  const form = useFormContext<CockpitFormValues>();

  return (
    <section className="space-y-3" {...testIdProps(testIds.encounters.plan)}>
      <h2 className="text-lg font-semibold">{t("plan.title")}</h2>
      <SelectField
        name="planDraftKind"
        label={t("plan.kind")}
        disabled={disabled}
        options={PLAN_KINDS.map((kind) => ({
          value: kind,
          label: planKindLabel(t, kind),
        }))}
      />
      <TextField
        name="planDraftDetail"
        label={t("plan.detail")}
        disabled={disabled}
      />
      <Button
        type="button"
        disabled={disabled}
        onClick={() => {
          const detail = form.getValues("planDraftDetail").trim();
          if (detail.length === 0) {
            return;
          }
          onAdd(form.getValues("planDraftKind"), detail);
          form.setValue("planDraftDetail", "");
        }}
        {...testIdProps(testIds.encounters.planAdd)}
      >
        {t("plan.add")}
      </Button>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("plan.empty")}</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex items-start justify-between gap-3 rounded-lg border border-border px-3 py-2"
            >
              <p className="text-sm">
                {t("plan.line", {
                  kind: planKindLabel(t, item.kind),
                  detail: item.detail,
                })}
              </p>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                disabled={disabled}
                onClick={() => onRemove(item.id)}
              >
                {t("plan.remove")}
              </Button>
            </li>
          ))}
        </ul>
      )}
      <TextAreaField
        name="planNote"
        label={t("plan.note")}
        disabled={disabled}
      />
    </section>
  );
}
