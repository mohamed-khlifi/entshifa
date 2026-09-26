import { DEFAULT_LOCALE, getLocaleDefinition } from "@/lib/i18n/config";

/**
 * Medical units are never translated. Pass them through as constants.
 * Surrounding words go through next-intl; units stay as-is.
 */
export const MEDICAL_UNITS = {
  dbHl: "dB HL",
  hz: "Hz",
  dapa: "daPa",
  ml: "mL",
  mg: "mg",
  mgPerKg: "mg/kg",
  mmHg: "mmHg",
  kg: "kg",
  mm: "mm",
} as const;

export type MedicalUnit = (typeof MEDICAL_UNITS)[keyof typeof MEDICAL_UNITS];

export type PersonName = {
  given?: string | null;
  family?: string | null;
  prefix?: string | null;
  suffix?: string | null;
};

function resolveIntlLocale(locale?: string): string {
  if (!locale) {
    return getLocaleDefinition(DEFAULT_LOCALE).intlLocale;
  }
  return getLocaleDefinition(locale).intlLocale;
}

export function formatDate(
  value: Date | string | number,
  locale?: string,
  options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
  },
): string {
  const date = value instanceof Date ? value : new Date(value);
  return new Intl.DateTimeFormat(resolveIntlLocale(locale), options).format(
    date,
  );
}

export function formatTime(
  value: Date | string | number,
  locale?: string,
  options: Intl.DateTimeFormatOptions = {
    hour: "2-digit",
    minute: "2-digit",
  },
): string {
  const date = value instanceof Date ? value : new Date(value);
  return new Intl.DateTimeFormat(resolveIntlLocale(locale), options).format(
    date,
  );
}

export function formatDateTime(
  value: Date | string | number,
  locale?: string,
  options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  },
): string {
  const date = value instanceof Date ? value : new Date(value);
  return new Intl.DateTimeFormat(resolveIntlLocale(locale), options).format(
    date,
  );
}

export function formatNumber(
  value: number,
  locale?: string,
  options?: Intl.NumberFormatOptions,
): string {
  return new Intl.NumberFormat(resolveIntlLocale(locale), options).format(
    value,
  );
}

export function formatDecimal(
  value: number,
  locale?: string,
  fractionDigits = 1,
): string {
  return formatNumber(value, locale, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

/**
 * Format a quantity with an untranslated medical unit.
 * Example: formatQuantity(25.5, MEDICAL_UNITS.dbHl, 'fr') → "25,5 dB HL"
 */
export function formatQuantity(
  value: number,
  unit: MedicalUnit | string,
  locale?: string,
  fractionDigits?: number,
): string {
  const amount =
    fractionDigits === undefined
      ? formatNumber(value, locale)
      : formatDecimal(value, locale, fractionDigits);
  return `${amount} ${unit}`;
}

/**
 * Western order for Latin locales; family-given for Arabic.
 */
export function formatPersonName(name: PersonName, locale?: string): string {
  const given = name.given?.trim() ?? "";
  const family = name.family?.trim() ?? "";
  const prefix = name.prefix?.trim() ?? "";
  const suffix = name.suffix?.trim() ?? "";
  const localeCode = getLocaleDefinition(locale ?? DEFAULT_LOCALE).code;

  const core =
    localeCode === "ar"
      ? [family, given].filter(Boolean).join(" ")
      : [given, family].filter(Boolean).join(" ");

  return [prefix, core, suffix].filter(Boolean).join(" ").trim();
}
