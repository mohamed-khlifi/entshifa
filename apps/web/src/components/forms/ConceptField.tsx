'use client';

import { Controller, useFormContext, type FieldPath, type FieldValues } from 'react-hook-form';

import { FormFieldShell } from '@/components/forms/FormFieldShell';
import type { SelectOption } from '@/components/forms/SelectField';
import { fieldTestId } from '@/lib/forms/field-test-id';
import { cn } from '@/lib/utils/cn';
import { testIdProps } from '@/lib/test/test-id';

export type ConceptFieldProps<T extends FieldValues> = {
  name: FieldPath<T>;
  label: string;
  /** Options resolved from terminology (value = concept public id or code). */
  options: readonly SelectOption[];
  description?: string;
  required?: boolean;
  placeholder?: string;
  /** Value set id for documentation / future dictionary fetch; not sent to DOM. */
  valueSet?: string;
  disabled?: boolean;
  className?: string;
};

export function ConceptField<T extends FieldValues>({
  name,
  label,
  options,
  description,
  required,
  placeholder,
  disabled,
  className,
}: ConceptFieldProps<T>) {
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
          <select
            id={inputId}
            disabled={disabled}
            aria-invalid={fieldState.invalid}
            className={cn(
              'flex h-11 w-full rounded-lg border border-input bg-card px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            )}
            {...testIdProps(inputId)}
            name={field.name}
            ref={field.ref}
            onBlur={field.onBlur}
            value={field.value ?? ''}
            onChange={(event) => field.onChange(event.target.value)}
          >
            {placeholder ? (
              <option value="" disabled={required}>
                {placeholder}
              </option>
            ) : null}
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </FormFieldShell>
      )}
    />
  );
}
