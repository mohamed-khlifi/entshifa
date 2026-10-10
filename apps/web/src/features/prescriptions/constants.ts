/** Closed values shared with the prescriptions API. */

export const PRESCRIPTION_ROUTES = [
  "oral",
  "nasal",
  "otic",
  "topical",
  "injection",
] as const;

export type PrescriptionRoute = (typeof PRESCRIPTION_ROUTES)[number];

export const PRESCRIPTION_STATUSES = ["draft", "issued", "cancelled"] as const;

export const PAPER_LOCALES = ["en", "fr", "ar"] as const;

export type PaperLocale = (typeof PAPER_LOCALES)[number];

export const ALLERGY_OVERRIDE = "prescription.allergy_conflict";
export const DOSE_OVERRIDE = "prescription.dose_above_maximum";
export const WEIGHT_BLOCK = "prescription.pediatric_weight_missing";
