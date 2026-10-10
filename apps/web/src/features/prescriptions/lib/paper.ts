import type {
  ClinicRead,
  PatientRead,
  PrescriptionItemRead,
} from "@/lib/api/generated";
import { formatDate, formatPersonName } from "@/lib/i18n/format";

import type { PaperLocale } from "../constants";
import type { ItemValues } from "./items";

export type PaperLine = {
  title: string;
  dose: string | null;
  unit: string | null;
  route: string;
  frequencyPerDay: number;
  durationDays: number;
  instructions: string | null;
  renewable: boolean;
  substitutionAllowed: boolean;
  taper: readonly { day: string; doseMg: string }[];
};

export type PaperModel = {
  clinicName: string;
  legalName: string | null;
  addressLines: readonly string[];
  phone: string | null;
  email: string | null;
  registrationNumber: string | null;
  taxId: string | null;
  patientName: string;
  birthDate: string;
  mrn: string;
  weightKg: string | null;
  identifier: string | null;
  lines: readonly PaperLine[];
};

export function clinicAddress(clinic: ClinicRead): string[] {
  return [
    clinic.addressLine1,
    clinic.addressLine2,
    [clinic.postalCode, clinic.city].filter(Boolean).join(" "),
    clinic.countryCode,
  ].filter((line): line is string => Boolean(line && line.trim().length > 0));
}

export function paperShell(
  clinic: ClinicRead,
  patient: PatientRead,
  locale: PaperLocale,
  weightKg: string | null,
  identifier: string | null,
  lines: readonly PaperLine[],
): PaperModel {
  return {
    clinicName: clinic.name,
    legalName: clinic.legalName ?? null,
    addressLines: clinicAddress(clinic),
    phone: clinic.phone ?? null,
    email: clinic.email ?? null,
    registrationNumber: clinic.registrationNumber ?? null,
    taxId: clinic.taxId ?? null,
    patientName: formatPersonName(
      { given: patient.firstName, family: patient.lastName },
      locale,
    ),
    birthDate: formatDate(patient.birthDate, locale),
    mrn: patient.mrn,
    weightKg,
    identifier,
    lines,
  };
}

export function taperFromSchedule(
  doses: readonly string[],
): PaperLine["taper"] {
  return doses.map((doseMg, index) => ({
    day: String(index + 1),
    doseMg,
  }));
}

export function taperFromRecord(
  schedule: PrescriptionItemRead["taperSchedule"],
): PaperLine["taper"] {
  if (!Array.isArray(schedule)) {
    return [];
  }
  return schedule.flatMap((row) => {
    if (typeof row !== "object" || row === null) {
      return [];
    }
    const record = row as Record<string, unknown>;
    const day = record.day;
    const doseMg = record.doseMg;
    if (day == null || doseMg == null) {
      return [];
    }
    return [{ day: String(day), doseMg: String(doseMg) }];
  });
}

export function lineFromDraft(
  item: ItemValues,
  taper: readonly string[],
): PaperLine {
  return {
    title: item.label || item.freeTextName,
    dose: item.doseAmount || null,
    unit: item.doseUnit || null,
    route: item.route,
    frequencyPerDay: Number(item.frequencyPerDay) || 0,
    durationDays: Number(item.durationDays) || 0,
    instructions: item.instructionsText.trim() || null,
    renewable: item.isRenewable,
    substitutionAllowed: item.substitutionAllowed,
    taper: taperFromSchedule(taper),
  };
}
