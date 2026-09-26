import { describe, expect, it } from 'vitest';

import {
  DEFAULT_LOCALE,
  PSEUDO_LOCALE,
  PRODUCTION_LOCALES,
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
import { toPseudoLocaleMessages, toPseudoLocaleString } from './pseudo';
import { directionalIconClass } from './directional-icon';

describe('i18n config', () => {
  it('registers production locales including Arabic', () => {
    expect(PRODUCTION_LOCALES).toEqual(['en', 'fr', 'ar']);
    expect(DEFAULT_LOCALE).toBe('en');
  });

  it('marks Arabic as RTL', () => {
    expect(getLocaleDirection('ar')).toBe('rtl');
    expect(isRtlLocale('ar')).toBe(true);
    expect(isRtlLocale('en')).toBe(false);
    expect(getLocaleDirection(PSEUDO_LOCALE)).toBe('ltr');
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
    expect(formatPersonName({ given: 'Sara', family: 'Hassan' }, 'ar')).toBe('Hassan Sara');
    expect(formatPersonName({ given: 'Sara', family: 'Hassan' }, 'en')).toBe('Sara Hassan');
  });
});

describe('pseudo locale', () => {
  it('adds accents and length while preserving placeholders', () => {
    const result = toPseudoLocaleString('Hello {name}');
    expect(result).toContain('{name}');
    expect(result.startsWith('Hélló')).toBe(true);
    expect(result.length).toBeGreaterThan('Hello {name}'.length);
  });

  it('transforms nested message trees', () => {
    const tree = toPseudoLocaleMessages({
      greeting: 'Welcome',
      nested: { label: 'Save' },
    });
    expect(tree.greeting).not.toBe('Welcome');
    expect(tree.nested.label).not.toBe('Save');
  });
});

describe('directionalIconClass', () => {
  it('adds the RTL flip utility', () => {
    expect(directionalIconClass('size-4')).toContain('rtl:-scale-x-100');
  });
});
