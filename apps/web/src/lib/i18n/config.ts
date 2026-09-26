/**
 * Locale registry: codes, direction, fonts, and which locales ship in production.
 * Adding a language is configuration here plus catalogs — not feature code.
 */

export const PRODUCTION_LOCALES = ['en', 'fr', 'ar'] as const;
export const PSEUDO_LOCALE = 'en-XA' as const;
export const DEFAULT_LOCALE = 'en' as const;

export type ProductionLocale = (typeof PRODUCTION_LOCALES)[number];
export type AppLocale = ProductionLocale | typeof PSEUDO_LOCALE;

export type TextDirection = 'ltr' | 'rtl';

export type LocaleDefinition = {
  code: AppLocale;
  /** Catalog directory for production locales; en-XA loads English then transforms. */
  catalogLocale: ProductionLocale;
  direction: TextDirection;
  /** BCP 47 tag used by Intl formatters. */
  intlLocale: string;
  /** next-intl message key under common.locale.options (no hyphens in JSON keys). */
  optionMessageKey: 'en' | 'fr' | 'ar' | 'enXA';
  /** Whether this locale is offered outside development. */
  isProduction: boolean;
};

const LOCALE_DEFINITIONS: Record<AppLocale, LocaleDefinition> = {
  en: {
    code: 'en',
    catalogLocale: 'en',
    direction: 'ltr',
    intlLocale: 'en-US',
    optionMessageKey: 'en',
    isProduction: true,
  },
  fr: {
    code: 'fr',
    catalogLocale: 'fr',
    direction: 'ltr',
    intlLocale: 'fr-FR',
    optionMessageKey: 'fr',
    isProduction: true,
  },
  ar: {
    code: 'ar',
    catalogLocale: 'ar',
    direction: 'rtl',
    intlLocale: 'ar',
    optionMessageKey: 'ar',
    isProduction: true,
  },
  [PSEUDO_LOCALE]: {
    code: PSEUDO_LOCALE,
    catalogLocale: 'en',
    direction: 'ltr',
    intlLocale: 'en-US',
    optionMessageKey: 'enXA',
    isProduction: false,
  },
};

export const MESSAGE_NAMESPACES = [
  'common',
  'auth',
  'errors',
  'forms',
  'data',
  'uiKit',
] as const;

export type MessageNamespace = (typeof MESSAGE_NAMESPACES)[number];

export function isPseudoLocaleEnabled(): boolean {
  return process.env.NODE_ENV !== 'production';
}

export function getEnabledLocales(): readonly AppLocale[] {
  if (isPseudoLocaleEnabled()) {
    return [...PRODUCTION_LOCALES, PSEUDO_LOCALE];
  }
  return PRODUCTION_LOCALES;
}

export function isAppLocale(value: string): value is AppLocale {
  return (getEnabledLocales() as readonly string[]).includes(value);
}

export function getLocaleDefinition(locale: string): LocaleDefinition {
  if (isAppLocale(locale)) {
    return LOCALE_DEFINITIONS[locale];
  }
  return LOCALE_DEFINITIONS[DEFAULT_LOCALE];
}

export function getLocaleDirection(locale: string): TextDirection {
  return getLocaleDefinition(locale).direction;
}

export function isRtlLocale(locale: string): boolean {
  return getLocaleDirection(locale) === 'rtl';
}

/** Locales that use the Arabic font stack (matching x-height with Latin). */
export function usesArabicFont(locale: string): boolean {
  return getLocaleDefinition(locale).catalogLocale === 'ar' || locale === 'ar';
}
