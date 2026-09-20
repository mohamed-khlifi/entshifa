import { describe, expect, it } from 'vitest';

import { publicIdTestId, testId, testIdProps, testIds } from './test-id';

describe('testId', () => {
  it('joins segments with dots', () => {
    expect(testId('auth', 'login', 'email')).toBe('auth.login.email');
  });

  it('rejects invalid segments', () => {
    expect(() => testId('Auth', 'login')).toThrow();
  });

  it('builds props object', () => {
    expect(testIdProps(testIds.auth.login.submit)).toEqual({
      'data-testid': 'auth.login.submit',
    });
  });

  it('embeds public ids in dynamic helpers', () => {
    expect(publicIdTestId('patients.list.row', '01ARZ3NDEKTSV4RRFFQ69G5FAV')).toBe(
      'patients.list.row.01ARZ3NDEKTSV4RRFFQ69G5FAV',
    );
  });
});
