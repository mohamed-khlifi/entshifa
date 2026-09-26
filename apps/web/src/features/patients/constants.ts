/** Safety flags stored on `patient_flag.flag_code` (P1-05). */

export const PATIENT_FLAG_CODES = [
  "only_hearing_ear",
  "anticoagulant",
  "ototoxic_therapy",
  "difficult_airway",
  "tracheostomy",
  "laryngeal_stenosis",
  "cochlear_implant",
  "pacemaker",
  "immunosuppressed",
  "diabetes",
  "pregnancy",
  "breastfeeding",
  "pediatric_weight_missing",
] as const;

export type PatientFlagCode = (typeof PATIENT_FLAG_CODES)[number];

export const ONLY_HEARING_EAR: PatientFlagCode = "only_hearing_ear";

export const SEX_VALUES = ["male", "female", "other", "unknown"] as const;
export type SexValue = (typeof SEX_VALUES)[number];

export const ALLERGY_CATEGORIES = ["drug", "food", "other"] as const;
export const ALLERGY_SEVERITIES = ["mild", "moderate", "severe"] as const;
export const MEDICATION_SOURCES = [
  "prescribed_here",
  "reported",
  "external",
] as const;
export const PROBLEM_STATUSES = [
  "active",
  "resolved",
  "suspected",
  "ruled_out",
] as const;
export const HISTORY_CATEGORIES = [
  "ent_surgery",
  "other_surgery",
  "medical",
  "family",
  "social",
  "obstetric",
] as const;
export const IDENTIFIER_TYPES = [
  "national_id",
  "passport",
  "insurance",
] as const;
