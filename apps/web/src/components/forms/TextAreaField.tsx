"use client";

import {
  Controller,
  useFormContext,
  type FieldPath,
  type FieldValues,
} from "react-hook-form";

import { FormFieldShell } from "@/components/forms/FormFieldShell";
import { fieldTestId } from "@/lib/forms/field-test-id";
import { testIdProps } from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

export type TextAreaFieldProps<T extends FieldValues> = {
  name: FieldPath<T>;
  label: string;
  description?: string;
  required?: boolean;
  rows?: number;
  disabled?: boolean;
  className?: string;
};

export function TextAreaField<T extends FieldValues>({
  name,
  label,
  description,
  required,
  rows = 4,
  disabled,
  className,
}: TextAreaFieldProps<T>) {
  const { control } = useFormContext<T>();
  const inputId = fieldTestId(name);

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
          htmlFor={inputId}
          className={className}
        >
          <textarea
            id={inputId}
            rows={rows}
            disabled={disabled}
            aria-invalid={fieldState.invalid}
            className={cn(
              "flex min-h-28 w-full rounded-lg border border-input bg-card px-3 py-2 text-sm shadow-sm ring-offset-background transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
            )}
            {...testIdProps(inputId)}
            name={field.name}
            ref={field.ref}
            onBlur={field.onBlur}
            value={field.value ?? ""}
            onChange={field.onChange}
          />
        </FormFieldShell>
      )}
    />
  );
}
