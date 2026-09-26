"use client";

import {
  Controller,
  useFormContext,
  type FieldPath,
  type FieldValues,
} from "react-hook-form";

import { FormFieldShell } from "@/components/forms/FormFieldShell";
import { Input } from "@/components/ui/input";
import { fieldTestId } from "@/lib/forms/field-test-id";
import { testIdProps } from "@/lib/test/test-id";

export type DateFieldProps<T extends FieldValues> = {
  name: FieldPath<T>;
  label: string;
  description?: string;
  required?: boolean;
  min?: string;
  max?: string;
  disabled?: boolean;
  className?: string;
};

export function DateField<T extends FieldValues>({
  name,
  label,
  description,
  required,
  min,
  max,
  disabled,
  className,
}: DateFieldProps<T>) {
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
          <Input
            id={inputId}
            type="date"
            min={min}
            max={max}
            disabled={disabled}
            aria-invalid={fieldState.invalid}
            {...testIdProps(inputId)}
            name={field.name}
            ref={field.ref}
            onBlur={field.onBlur}
            value={field.value ?? ""}
            onChange={(event) => field.onChange(event.target.value)}
          />
        </FormFieldShell>
      )}
    />
  );
}
