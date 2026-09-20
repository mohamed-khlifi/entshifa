import { describe, expect, it } from 'vitest';

import { ApiError, resolveErrorMessage } from './errors';

describe('resolveErrorMessage', () => {
  it('maps known error codes through the translator', () => {
    const error = new ApiError({
      code: 'auth.invalid_credentials',
      status: 401,
      context: {},
    });
    const message = resolveErrorMessage(error, (key) =>
      key === 'auth.invalid_credentials' ? 'Invalid credentials' : key === 'generic' ? 'Something went wrong' : key,
    );
    expect(message).toBe('Invalid credentials');
  });

  it('falls back to generic when code is unknown', () => {
    const error = new ApiError({
      code: 'unknown.problem',
      status: 400,
      context: {},
    });
    const message = resolveErrorMessage(error, (key) =>
      key === 'generic' ? 'Something went wrong' : key,
    );
    expect(message).toBe('Something went wrong');
  });
});
