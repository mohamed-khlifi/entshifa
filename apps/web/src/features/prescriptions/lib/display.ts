import type { CalculationRead } from "@/lib/api/generated";

import { PAPER_LOCALES, type PaperLocale } from "../constants";

export function flagValue(
  calculation: CalculationRead,
  code: string,
): string | null {
  const flag = calculation.flags.find((item) => item.code === code);
  const value = flag?.detail.value;
  return value && value.length > 0 ? value : null;
}

export function flagUnit(
  calculation: CalculationRead,
  code: string,
): string | null {
  const flag = calculation.flags.find((item) => item.code === code);
  const unit = flag?.detail.unit;
  return unit && unit.length > 0 ? unit : null;
}

/** Server-produced comma-separated milligram list. No dose is computed here. */
export function scheduleDoses(calculation: CalculationRead): string[] {
  const flag = calculation.flags.find((item) => item.code === "schedule_mg");
  const days = flag?.detail.days;
  if (!days) {
    return [];
  }
  return days
    .split(",")
    .map((part) => part.trim())
    .filter((part) => part.length > 0);
}

export function paperLocale(
  preferred: string | null | undefined,
  clinicDefault: string | null | undefined,
): PaperLocale {
  if (preferred && isPaperLocale(preferred)) {
    return preferred;
  }
  if (clinicDefault && isPaperLocale(clinicDefault)) {
    return clinicDefault;
  }
  return "en";
}

function isPaperLocale(value: string): value is PaperLocale {
  return (PAPER_LOCALES as readonly string[]).includes(value);
}
