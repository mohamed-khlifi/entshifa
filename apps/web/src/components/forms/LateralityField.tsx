"use client";

import { useTranslations } from "next-intl";
import {
  Controller,
  useFormContext,
  type FieldPath,
  type FieldValues,
} from "react-hook-form";

import { FormFieldShell } from "@/components/forms/FormFieldShell";
import { fieldNameSegments, fieldTestId } from "@/lib/forms/field-test-id";
import { cn } from "@/lib/utils/cn";
import { testId, testIdProps } from "@/lib/test/test-id";

export const LATERALITY_VALUES = [
  "left",
  "right",
  "bilateral",
  "unspecified",
] as const;
export type LateralityValue = (typeof LATERALITY_VALUES)[number];

const LATERALITY_LABEL_KEYS = {
  left: "laterality.left",
  right: "laterality.right",
  bilateral: "laterality.bilateral",
  unspecified: "laterality.unspecified",
} as const satisfies Record<LateralityValue, `laterality.${LateralityValue}`>;

export type LateralityFieldProps<T extends FieldValues> = {
  name: FieldPath<T>;
  label: string;
  description?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
};

export function LateralityField<T extends FieldValues>({
  name,
  label,
  description,
  required,
  disabled,
  className,
}: LateralityFieldProps<T>) {
  const { control } = useFormContext<T>();
  const t = useTranslations("forms");
  const groupId = fieldTestId(name);

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState }) => (
        <FormFieldShell
          name={name}
          label={label}
          description={description}
          required={required}
          error={fieldState.error?.message}
          htmlFor={groupId}
          className={className}
        >
          <div
            id={groupId}
            role="radiogroup"
            aria-invalid={fieldState.invalid}
            className="flex flex-wrap gap-2"
            {...testIdProps(groupId)}
          >
            {LATERALITY_VALUES.map((value) => {
              const optionId = testId(
                "forms",
                "field",
                ...fieldNameSegments(name),
                value,
              );
              const selected = field.value === value;
              return (
                <label
                  key={value}
                  htmlFor={optionId}
                  className={cn(
                    "inline-flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors",
                    selected
                      ? "border-primary bg-accent text-accent-foreground"
                      : "border-input bg-card text-foreground hover:bg-accent/40",
                    disabled && "cursor-not-allowed opacity-50",
                  )}
                >
                  <input
                    id={optionId}
                    type="radio"
                    className="sr-only"
                    disabled={disabled}
                    checked={selected}
                    onChange={() => field.onChange(value)}
                    onBlur={field.onBlur}
                    name={field.name}
                    value={value}
                    {...testIdProps(optionId)}
                  />
                  {t(LATERALITY_LABEL_KEYS[value])}
                </label>
              );
            })}
          </div>
        </FormFieldShell>
      )}
    />
  );
}
