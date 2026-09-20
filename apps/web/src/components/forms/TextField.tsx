'use client';

import { Controller, useFormContext, type FieldPath, type FieldValues } from 'react-hook-form';

import { FormFieldShell } from '@/components/forms/FormFieldShell';
import { Input } from '@/components/ui/input';
import { fieldTestId } from '@/lib/forms/field-test-id';
import { testIdProps } from '@/lib/test/test-id';

export type TextFieldProps<T extends FieldValues> = {
  name: FieldPath<T>;
  label: string;
  description?: string;
  required?: boolean;
  unit?: string;
  type?: 'text' | 'email' | 'password' | 'tel' | 'search';
  autoComplete?: string;
  disabled?: boolean;
  className?: string;
};

export function TextField<T extends FieldValues>({
  name,
  label,
  description,
  required,
  unit,
  type = 'text',
  autoComplete,
  disabled,
  className,
}: TextFieldProps<T>) {
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
            type={type}
            autoComplete={autoComplete}
            disabled={disabled}
            aria-invalid={fieldState.invalid}
            {...testIdProps(inputId)}
            {...field}
            value={field.value ?? ''}
          />
        </FormFieldShell>
      )}
    />
  );
}
