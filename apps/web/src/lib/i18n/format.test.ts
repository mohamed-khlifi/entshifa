import { describe, expect, it } from 'vitest';

import {
  DEFAULT_LOCALE,
  LOCALES,
  getLocaleDirection,
  isRtlLocale,
} from './config';
import {
  MEDICAL_UNITS,
  formatDate,
  formatDecimal,
  formatNumber,
  formatPersonName,
  formatQuantity,
} from './format';
import { directionalIconClass } from './directional-icon';

describe('i18n config', () => {
  it('registers en, fr, and ar', () => {
    expect(LOCALES).toEqual(['en', 'fr', 'ar']);
    expect(DEFAULT_LOCALE).toBe('en');
  });

  it('marks Arabic as RTL', () => {
    expect(getLocaleDirection('ar')).toBe('rtl');
    expect(isRtlLocale('ar')).toBe(true);
    expect(isRtlLocale('en')).toBe(false);
  });
});

describe('format helpers', () => {
  it('formats French decimals with a comma', () => {
    expect(formatDecimal(25.5, 'fr', 1)).toBe('25,5');
  });

  it('formats English numbers without translating units', () => {
    expect(formatQuantity(40, MEDICAL_UNITS.dbHl, 'en', 0)).toBe('40 dB HL');
    expect(formatNumber(1234.5, 'en')).toMatch(/1,234\.5|1 234/);
  });

  it('formats dates for the requested locale', () => {
    const value = new Date(Date.UTC(2024, 0, 15));
    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: 'UTC',
    };
    const en = formatDate(value, 'en', options);
    const fr = formatDate(value, 'fr', options);
    expect(en).toMatch(/Jan/);
    expect(fr.toLowerCase()).toMatch(/janv/);
  });

  it('orders Arabic names family-given', () => {
    expect(formatPersonName({ given: 'Sara', family: 'Hassan' }, 'ar')).toBe(
      'Hassan Sara',
    );
    expect(formatPersonName({ given: 'Sara', family: 'Hassan' }, 'en')).toBe(
      'Sara Hassan',
    );
  });
});

describe('directionalIconClass', () => {
  it('adds the RTL flip utility', () => {
    expect(directionalIconClass('size-4')).toContain('rtl:-scale-x-100');
  });
});
