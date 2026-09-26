/**
 * Locale registry: codes, direction, and fonts.
 * Adding a language is configuration here plus catalogs — not feature code.
 */

export const LOCALES = ["en", "fr", "ar"] as const;
export const DEFAULT_LOCALE = "en" as const;

export type AppLocale = (typeof LOCALES)[number];
export type TextDirection = "ltr" | "rtl";

export type LocaleDefinition = {
  code: AppLocale;
  direction: TextDirection;
  /** BCP 47 tag used by Intl formatters. */
  intlLocale: string;
};

const LOCALE_DEFINITIONS: Record<AppLocale, LocaleDefinition> = {
  en: {
    code: "en",
    direction: "ltr",
    intlLocale: "en-US",
  },
  fr: {
    code: "fr",
    direction: "ltr",
    intlLocale: "fr-FR",
  },
  ar: {
    code: "ar",
    direction: "rtl",
    intlLocale: "ar",
  },
};

export const MESSAGE_NAMESPACES = [
  "common",
  "auth",
  "errors",
  "forms",
  "data",
  "uiKit",
  "attachments",
] as const;

export type MessageNamespace = (typeof MESSAGE_NAMESPACES)[number];

export function isAppLocale(value: string): value is AppLocale {
  return (LOCALES as readonly string[]).includes(value);
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
  return getLocaleDirection(locale) === "rtl";
}

/** Locales that use the Arabic font stack (matching x-height with Latin). */
export function usesArabicFont(locale: string): boolean {
  return getLocaleDefinition(locale).code === "ar";
}
