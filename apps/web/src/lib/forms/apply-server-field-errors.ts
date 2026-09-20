import type { FieldPath, FieldValues, UseFormReturn } from 'react-hook-form';

import { ApiError, apiErrorCodeToMessageKey } from '@/lib/api/errors';

export type FieldErrorTranslator = (
  code: string,
  field: string,
) => string;

/**
 * Maps API `context.fieldErrors` onto react-hook-form field errors.
 * Values are error codes (translated); never raw server sentences.
 */
export function applyServerFieldErrors<T extends FieldValues>(
  form: UseFormReturn<T>,
  error: ApiError,
  translate: FieldErrorTranslator,
): boolean {
  const raw = error.context.fieldErrors;
  if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) {
    return false;
  }

  let applied = false;
  for (const [field, code] of Object.entries(raw as Record<string, unknown>)) {
    if (typeof code !== 'string' || code.length === 0) {
      continue;
    }
    const messageKey = apiErrorCodeToMessageKey(code);
    form.setError(field as FieldPath<T>, {
      type: 'server',
      message: translate(messageKey, field),
    });
    applied = true;
  }
  return applied;
}
