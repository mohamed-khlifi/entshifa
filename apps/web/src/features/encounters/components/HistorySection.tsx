"use client";

import { useTranslations } from "next-intl";
import { useFormContext, type FieldPath } from "react-hook-form";

import { NumberField } from "@/components/forms/NumberField";
import { SelectField } from "@/components/forms/SelectField";
import { TextAreaField } from "@/components/forms/TextAreaField";
import { TextField } from "@/components/forms/TextField";
import { ScaleField } from "@/components/forms/ScaleField";
import { Button } from "@/components/ui/button";
import { testIdProps, testIds } from "@/lib/test/test-id";

import { courseLabel, historyLateralityLabel } from "../lib/labels";
import {
  templateFieldLabel,
  templateOptionLabel,
} from "../lib/template-labels";
import type { HistoryFieldConfig } from "../lib/template-config";
import type { CockpitFormValues } from "../schemas/cockpit.schema";

type HistorySectionProps = {
  fields: readonly HistoryFieldConfig[];
  disabled: boolean;
};

export function HistorySection({ fields, disabled }: HistorySectionProps) {
  const t = useTranslations("encounters");
  const form = useFormContext<CockpitFormValues>();
  const answers = form.watch("templateAnswers");

  function setAnswer(
    id: string,
    value: CockpitFormValues["templateAnswers"][string],
  ) {
    form.setValue(
      "templateAnswers",
      { ...form.getValues("templateAnswers"), [id]: value },
      { shouldDirty: true },
    );
  }

  return (
    <section className="space-y-4" {...testIdProps(testIds.encounters.history)}>
      <h2 className="text-lg font-semibold">{t("history.title")}</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        <TextField
          name="onset"
          label={t("history.onset")}
          disabled={disabled}
        />
        <SelectField
          name="course"
          label={t("history.course")}
          disabled={disabled}
          placeholder={t("history.course")}
          options={[
            { value: "constant", label: courseLabel(t, "constant") },
            { value: "intermittent", label: courseLabel(t, "intermittent") },
            { value: "progressive", label: courseLabel(t, "progressive") },
            { value: "improving", label: courseLabel(t, "improving") },
          ]}
        />
        <SelectField
          name="laterality"
          label={t("history.laterality")}
          disabled={disabled}
          placeholder={t("history.laterality")}
          options={[
            { value: "right", label: historyLateralityLabel(t, "right") },
            { value: "left", label: historyLateralityLabel(t, "left") },
            {
              value: "bilateral",
              label: historyLateralityLabel(t, "bilateral"),
            },
            {
              value: "alternating",
              label: historyLateralityLabel(t, "alternating"),
            },
          ]}
        />
        <ScaleField
          name="severity"
          label={t("history.severity")}
          disabled={disabled}
        />
        <TextField
          name="triggers"
          label={t("history.triggers")}
          disabled={disabled}
        />
        <TextField
          name="relievingFactors"
          label={t("history.relievingFactors")}
          disabled={disabled}
        />
      </div>
      <TextAreaField
        name="previousTreatments"
        label={t("history.previousTreatments")}
        disabled={disabled}
      />
      <TextAreaField
        name="previousConsultations"
        label={t("history.previousConsultations")}
        disabled={disabled}
      />
      <TextField
        name="impact"
        label={t("history.impact")}
        disabled={disabled}
      />
      {fields.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-sm font-medium">{t("history.templateTitle")}</h3>
          {fields.map((field) => (
            <TemplateField
              key={field.id}
              field={field}
              disabled={disabled}
              value={answers[field.id]}
              onChange={(value) => setAnswer(field.id, value)}
            />
          ))}
        </div>
      ) : null}
      <TextAreaField
        name="historyNote"
        label={t("history.note")}
        disabled={disabled}
        rows={5}
      />
    </section>
  );
}

function TemplateField({
  field,
  disabled,
  value,
  onChange,
}: {
  field: HistoryFieldConfig;
  disabled: boolean;
  value: CockpitFormValues["templateAnswers"][string] | undefined;
  onChange: (value: CockpitFormValues["templateAnswers"][string]) => void;
}) {
  const t = useTranslations("encounters");
  const label = templateFieldLabel(t, field.labelKey);
  const name = `templateAnswers.${field.id}` as FieldPath<CockpitFormValues>;

  if (field.fieldType === "boolean") {
    return (
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium">{label}</span>
        <Button
          type="button"
          variant={value === true ? "default" : "secondary"}
          disabled={disabled}
          aria-pressed={value === true}
          onClick={() => onChange(true)}
        >
          {t("history.yes")}
        </Button>
        <Button
          type="button"
          variant={value === false ? "default" : "secondary"}
          disabled={disabled}
          aria-pressed={value === false}
          onClick={() => onChange(false)}
        >
          {t("history.no")}
        </Button>
      </div>
    );
  }

  if (field.fieldType === "number") {
    return (
      <NumberField name={name} label={label} disabled={disabled} min={0} />
    );
  }

  if (field.fieldType === "select" || field.fieldType === "multiselect") {
    const options = (field.options ?? []).map((option) => ({
      value: option,
      label: templateOptionLabel(t, field.id, option),
    }));
    if (field.fieldType === "select") {
      return (
        <SelectField
          name={name}
          label={label}
          disabled={disabled}
          placeholder={label}
          options={options}
        />
      );
    }
    const selected = Array.isArray(value) ? value : [];
    return (
      <div className="space-y-2">
        <p className="text-sm font-medium">{label}</p>
        <div className="flex flex-wrap gap-2">
          {options.map((option) => {
            const pressed = selected.includes(option.value);
            return (
              <Button
                key={option.value}
                type="button"
                variant={pressed ? "default" : "secondary"}
                disabled={disabled}
                aria-pressed={pressed}
                onClick={() =>
                  onChange(
                    pressed
                      ? selected.filter((item) => item !== option.value)
                      : [...selected, option.value],
                  )
                }
              >
                {option.label}
              </Button>
            );
          })}
        </div>
      </div>
    );
  }

  return <TextField name={name} label={label} disabled={disabled} />;
}
