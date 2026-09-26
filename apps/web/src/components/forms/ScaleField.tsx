"use client";

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

export type ScaleFieldProps<T extends FieldValues> = {
  name: FieldPath<T>;
  label: string;
  description?: string;
  required?: boolean;
  min?: number;
  max?: number;
  disabled?: boolean;
  className?: string;
};

export function ScaleField<T extends FieldValues>({
  name,
  label,
  description,
  required,
  min = 0,
  max = 10,
  disabled,
  className,
}: ScaleFieldProps<T>) {
  const { control } = useFormContext<T>();
  const groupId = fieldTestId(name);
  const values = Array.from(
    { length: max - min + 1 },
    (_, index) => min + index,
  );

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
            className="flex flex-wrap gap-1.5"
            {...testIdProps(groupId)}
          >
            {values.map((value) => {
              const optionId = testId(
                "forms",
                "field",
                ...fieldNameSegments(name),
                `n${value < 0 ? `m${Math.abs(value)}` : String(value)}`,
              );
              const selected = field.value === value;
              return (
                <label
                  key={value}
                  htmlFor={optionId}
                  className={cn(
                    "inline-flex size-9 cursor-pointer items-center justify-center rounded-lg border text-sm font-medium transition-colors",
                    selected
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-input bg-card hover:bg-accent/40",
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
                  {value}
                </label>
              );
            })}
          </div>
        </FormFieldShell>
      )}
    />
  );
}
