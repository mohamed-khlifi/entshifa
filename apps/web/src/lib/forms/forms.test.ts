import { describe, expect, it } from 'vitest';

import { ApiError } from '@/lib/api/errors';
import { applyServerFieldErrors } from '@/lib/forms/apply-server-field-errors';
import { pickDirtyValues } from '@/lib/forms/autosave';
import {
  columnTestId,
  fieldErrorTestId,
  fieldNameSegments,
  fieldTestId,
} from '@/lib/forms/field-test-id';

describe('fieldTestId', () => {
  it('maps camelCase and dotted paths to stable ids', () => {
    expect(fieldNameSegments('lastName')).toEqual(['last-name']);
    expect(fieldNameSegments('thresholds.0.value')).toEqual([
      'thresholds',
      'i0',
      'value',
    ]);
    expect(fieldTestId('lastName')).toBe('forms.field.last-name');
    expect(fieldErrorTestId('weightKg')).toBe('forms.field-error.weight-kg');
    expect(columnTestId('birthDate')).toBe('data.table.col.birth-date');
  });
});

describe('pickDirtyValues', () => {
  it('returns only dirty keys', () => {
    expect(
      pickDirtyValues(
        { a: 1, b: 2, c: 3 },
        { a: true, c: { nested: true } },
      ),
    ).toEqual({ a: 1, c: 3 });
  });
});

describe('applyServerFieldErrors', () => {
  it('sets translated messages from context.fieldErrors', () => {
    const calls: Array<{ name: string; message: string }> = [];
    const form = {
      setError: (name: string, error: { message?: string }) => {
        calls.push({ name, message: error.message ?? '' });
      },
    };

    const applied = applyServerFieldErrors(
      form as never,
      new ApiError({
        code: 'validation_failed',
        status: 422,
        context: {
          fieldErrors: {
            lastName: 'validation_failed',
            'thresholds.0.value': 'out_of_range',
          },
        },
      }),
      (code) => (code === 'out_of_range' ? 'Out of range' : 'Invalid'),
    );

    expect(applied).toBe(true);
    expect(calls).toEqual([
      { name: 'lastName', message: 'Invalid' },
      { name: 'thresholds.0.value', message: 'Out of range' },
    ]);
  });

  it('returns false when fieldErrors are missing', () => {
    const form = { setError: () => undefined };
    expect(
      applyServerFieldErrors(
        form as never,
        new ApiError({ code: 'validation_failed', status: 422, context: {} }),
        (code) => code,
      ),
    ).toBe(false);
  });
});
