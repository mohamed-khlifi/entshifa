'use client';

import { Controller, useFormContext, type FieldPath, type FieldValues } from 'react-hook-form';

import { FormFieldShell } from '@/components/forms/FormFieldShell';
import { Input } from '@/components/ui/input';
import { fieldTestId } from '@/lib/forms/field-test-id';
import { testIdProps } from '@/lib/test/test-id';

export type NumberFieldProps<T extends FieldValues> = {
  name: FieldPath<T>;
  label: string;
  description?: string;
  required?: boolean;
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  className?: string;
};

export function NumberField<T extends FieldValues>({
  name,
  label,
  description,
  required,
  unit,
  min,
  max,
  step,
  disabled,
  className,
}: NumberFieldProps<T>) {
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
          unit={unit}
          error={fieldState.error?.message}
          htmlFor={inputId}
          className={className}
        >
          <Input
            id={inputId}
            type="number"
            inputMode="decimal"
            min={min}
            max={max}
            step={step}
            disabled={disabled}
            aria-invalid={fieldState.invalid}
            {...testIdProps(inputId)}
            name={field.name}
            ref={field.ref}
            onBlur={field.onBlur}
            value={field.value === undefined || field.value === null ? '' : String(field.value)}
            onChange={(event) => {
              const raw = event.target.value;
              if (raw === '') {
                field.onChange(undefined);
                return;
              }
              const parsed = Number(raw);
              field.onChange(Number.isFinite(parsed) ? parsed : undefined);
            }}
          />
        </FormFieldShell>
      )}
    />
  );
}
