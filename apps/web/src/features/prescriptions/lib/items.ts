import type {
  PrescriptionItemWrite,
  SafetyOverrideWrite,
  TaperWrite,
} from "@/lib/api/generated";

import {
  ALLERGY_OVERRIDE,
  DOSE_OVERRIDE,
  type PrescriptionRoute,
} from "../constants";
import { isRoute } from "./labels";

export type ItemValues = {
  key: string;
  formularyEntryPublicId: string;
  freeTextName: string;
  label: string;
  doseAmount: string;
  doseUnit: string;
  route: PrescriptionRoute;
  frequencyPerDay: string;
  durationDays: string;
  quantity: string;
  instructionsText: string;
  isRenewable: boolean;
  substitutionAllowed: boolean;
  calculateFromFormulary: boolean;
  indicationCode: string;
  useFormularyTaper: boolean;
  taperStartMg: string;
  taperStepMg: string;
  taperDaysPerStep: string;
  taperMinimumMg: string;
  allergyOverride: string;
  doseOverride: string;
};

export type PrescriptionFormValues = {
  isPediatric: boolean;
  weightKg: string;
  notes: string;
  items: ItemValues[];
};

const ULID = /^[0-9A-HJKMNP-TV-Z]{26}$/;
const POSITIVE_DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;

export function emptyItem(key: string): ItemValues {
  return {
    key,
    formularyEntryPublicId: "",
    freeTextName: "",
    label: "",
    doseAmount: "",
    doseUnit: "mg",
    route: "oral",
    frequencyPerDay: "1",
    durationDays: "7",
    quantity: "",
    instructionsText: "",
    isRenewable: false,
    substitutionAllowed: true,
    calculateFromFormulary: false,
    indicationCode: "",
    useFormularyTaper: false,
    taperStartMg: "",
    taperStepMg: "",
    taperDaysPerStep: "",
    taperMinimumMg: "",
    allergyOverride: "",
    doseOverride: "",
  };
}

export function appendInstruction(current: string, note: string): string {
  const next = note.trim();
  if (next.length === 0) {
    return current;
  }
  const base = current.trim();
  return base.length === 0 ? next : `${base}\n${next}`;
}

function wholeNumber(value: string, min: number, max: number): number | null {
  if (!/^\d+$/.test(value)) {
    return null;
  }
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    return null;
  }
  return parsed;
}

function taperWrite(item: ItemValues): TaperWrite | null {
  const started = [
    item.taperStartMg,
    item.taperStepMg,
    item.taperDaysPerStep,
    item.taperMinimumMg,
  ].some((part) => part.trim().length > 0);
  if (!started) {
    return null;
  }
  if (
    !POSITIVE_DECIMAL.test(item.taperStartMg) ||
    !POSITIVE_DECIMAL.test(item.taperStepMg) ||
    !POSITIVE_DECIMAL.test(item.taperMinimumMg || "0")
  ) {
    return null;
  }
  const days = wholeNumber(item.taperDaysPerStep, 1, 31);
  if (days == null) {
    return null;
  }
  return {
    startMg: item.taperStartMg,
    stepMg: item.taperStepMg,
    daysPerStep: days,
    minimumMg: item.taperMinimumMg || "0",
  };
}

export function itemWrite(
  item: ItemValues,
  sortOrder: number,
): PrescriptionItemWrite | null {
  const formularyId = item.formularyEntryPublicId.trim();
  const freeText = item.freeTextName.trim();
  const hasFormulary = ULID.test(formularyId);
  const hasText = freeText.length > 0;
  if (hasFormulary === hasText) {
    return null;
  }
  const frequency = wholeNumber(item.frequencyPerDay, 1, 24);
  const duration = wholeNumber(item.durationDays, 1, 3650);
  if (frequency == null || duration == null || !isRoute(item.route)) {
    return null;
  }
  const taper = item.useFormularyTaper ? null : taperWrite(item);
  const taperStarted =
    !item.useFormularyTaper &&
    [
      item.taperStartMg,
      item.taperStepMg,
      item.taperDaysPerStep,
      item.taperMinimumMg,
    ].some((part) => part.trim().length > 0);
  if (taperStarted && taper == null) {
    return null;
  }
  if (item.useFormularyTaper && !hasFormulary) {
    return null;
  }
  if (!item.calculateFromFormulary) {
    if (
      !POSITIVE_DECIMAL.test(item.doseAmount) ||
      item.doseUnit.trim().length === 0
    ) {
      return null;
    }
  } else if (!hasFormulary) {
    return null;
  }

  const overrides: SafetyOverrideWrite[] = [];
  if (item.allergyOverride.trim().length > 0) {
    overrides.push({
      code: ALLERGY_OVERRIDE,
      reason: item.allergyOverride.trim(),
    });
  }
  if (item.doseOverride.trim().length > 0) {
    overrides.push({
      code: DOSE_OVERRIDE,
      reason: item.doseOverride.trim(),
    });
  }

  return {
    formularyEntryPublicId: hasFormulary ? formularyId : null,
    freeTextName: hasText ? freeText : null,
    doseAmount: item.calculateFromFormulary ? null : item.doseAmount,
    doseUnit: item.calculateFromFormulary ? null : item.doseUnit.trim(),
    route: item.route,
    frequencyPerDay: frequency,
    durationDays: duration,
    quantity: item.quantity.trim() || null,
    instructionsText: item.instructionsText.trim() || null,
    isRenewable: item.isRenewable,
    substitutionAllowed: item.substitutionAllowed,
    sortOrder,
    calculateFromFormulary: item.calculateFromFormulary,
    indicationCode: item.indicationCode.trim() || null,
    taper,
    useFormularyTaper: item.useFormularyTaper,
    safetyOverrides: overrides,
  };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
}

function asText(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  return "";
}

export type StoredTaper = {
  startMg: string;
  stepMg: string;
  daysPerStep: string;
  minimumMg: string;
};

export function readStoredTaper(rules: unknown): StoredTaper | null {
  const document = asRecord(rules);
  const taper = asRecord(document?.taper);
  if (!taper) {
    return null;
  }
  const startMg = asText(taper.start_mg);
  const stepMg = asText(taper.step_mg);
  const daysPerStep = asText(taper.days_per_step);
  const minimumMg = asText(taper.minimum_mg);
  if (!startMg || !stepMg || !daysPerStep) {
    return null;
  }
  return { startMg, stepMg, daysPerStep, minimumMg: minimumMg || "0" };
}

export function readDefaultDuration(rules: unknown): string | null {
  const document = asRecord(rules);
  const value = asText(document?.default_duration_days);
  return value || null;
}

export function readIndicationCodes(rules: unknown): string[] {
  const document = asRecord(rules);
  const indications = asRecord(document?.indications);
  if (!indications) {
    return [];
  }
  return Object.keys(indications).filter((code) => /^[a-z0-9_]+$/.test(code));
}

export function itemFromTemplate(raw: unknown, key: string): ItemValues | null {
  const row = asRecord(raw);
  if (!row) {
    return null;
  }
  const base = emptyItem(key);
  const route = asText(row.route);
  const taper = asRecord(row.taper);
  return {
    ...base,
    formularyEntryPublicId: asText(row.formularyEntryPublicId),
    freeTextName: asText(row.freeTextName),
    label: asText(row.freeTextName),
    doseAmount: asText(row.doseAmount),
    doseUnit: asText(row.doseUnit) || "mg",
    route: isRoute(route) ? route : "oral",
    frequencyPerDay: asText(row.frequencyPerDay) || "1",
    durationDays: asText(row.durationDays) || "7",
    quantity: asText(row.quantity),
    instructionsText: asText(row.instructionsText),
    isRenewable: row.isRenewable === true,
    substitutionAllowed: row.substitutionAllowed !== false,
    calculateFromFormulary: row.calculateFromFormulary === true,
    indicationCode: asText(row.indicationCode),
    useFormularyTaper: row.useFormularyTaper === true,
    taperStartMg: asText(taper?.startMg),
    taperStepMg: asText(taper?.stepMg),
    taperDaysPerStep: asText(taper?.daysPerStep),
    taperMinimumMg: asText(taper?.minimumMg),
  };
}
