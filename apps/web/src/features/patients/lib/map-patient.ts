import type {
  PatientCreate,
  PatientRead,
  PatientUpdate,
} from "@/lib/api/generated";
import type { PatientFormValues } from "../schemas/patient-form.schema";

function blankToNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length === 0 ? null : trimmed;
}

export function patientToFormValues(patient: PatientRead): PatientFormValues {
  return {
    mrn: patient.mrn,
    firstName: patient.firstName,
    lastName: patient.lastName,
    firstNameAlt: patient.firstNameAlt ?? "",
    lastNameAlt: patient.lastNameAlt ?? "",
    birthDate: patient.birthDate,
    birthDateIsEstimated: patient.birthDateIsEstimated,
    sex: patient.sex as PatientFormValues["sex"],
    preferredLocale: patient.preferredLocale,
    phonePrimary: patient.phonePrimary ?? "",
    phoneSecondary: patient.phoneSecondary ?? "",
    email: patient.email ?? "",
    addressLine1: patient.addressLine1 ?? "",
    addressLine2: patient.addressLine2 ?? "",
    city: patient.city ?? "",
    postalCode: patient.postalCode ?? "",
    countryCode: patient.countryCode ?? "",
    occupation: patient.occupation ?? "",
    noiseExposure: patient.noiseExposure ?? "",
    smokingStatus: patient.smokingStatus ?? "",
    alcoholStatus: patient.alcoholStatus ?? "",
    insuranceNumber: patient.insuranceNumber ?? "",
    referringDoctorName: patient.referringDoctorName ?? "",
    referringDoctorPhone: patient.referringDoctorPhone ?? "",
    referringDoctorEmail: patient.referringDoctorEmail ?? "",
    referringDoctorLocale: patient.referringDoctorLocale ?? "",
    guardianName: patient.guardianName ?? "",
    guardianRelation: patient.guardianRelation ?? "",
    emergencyContactName: patient.emergencyContactName ?? "",
    emergencyContactPhone: patient.emergencyContactPhone ?? "",
    consentSms: patient.consentSms,
    consentEmail: patient.consentEmail,
    consentTeaching: patient.consentTeaching,
    isDeceased: patient.isDeceased,
    deceasedDate: patient.deceasedDate ?? "",
  };
}

export function formValuesToCreate(
  values: PatientFormValues,
  confirmDuplicate: boolean,
): PatientCreate {
  return {
    mrn: blankToNull(values.mrn),
    firstName: values.firstName.trim(),
    lastName: values.lastName.trim(),
    firstNameAlt: blankToNull(values.firstNameAlt),
    lastNameAlt: blankToNull(values.lastNameAlt),
    birthDate: values.birthDate,
    birthDateIsEstimated: values.birthDateIsEstimated,
    sex: values.sex,
    preferredLocale: values.preferredLocale.trim(),
    phonePrimary: blankToNull(values.phonePrimary),
    phoneSecondary: blankToNull(values.phoneSecondary),
    email: blankToNull(values.email),
    addressLine1: blankToNull(values.addressLine1),
    addressLine2: blankToNull(values.addressLine2),
    city: blankToNull(values.city),
    postalCode: blankToNull(values.postalCode),
    countryCode: blankToNull(values.countryCode)?.toUpperCase() ?? null,
    occupation: blankToNull(values.occupation),
    noiseExposure: blankToNull(values.noiseExposure),
    smokingStatus: blankToNull(values.smokingStatus),
    alcoholStatus: blankToNull(values.alcoholStatus),
    insuranceNumber: blankToNull(values.insuranceNumber),
    referringDoctorName: blankToNull(values.referringDoctorName),
    referringDoctorPhone: blankToNull(values.referringDoctorPhone),
    referringDoctorEmail: blankToNull(values.referringDoctorEmail),
    referringDoctorLocale: blankToNull(values.referringDoctorLocale),
    guardianName: blankToNull(values.guardianName),
    guardianRelation: blankToNull(values.guardianRelation),
    emergencyContactName: blankToNull(values.emergencyContactName),
    emergencyContactPhone: blankToNull(values.emergencyContactPhone),
    consentSms: values.consentSms,
    consentEmail: values.consentEmail,
    consentTeaching: values.consentTeaching,
    isDeceased: values.isDeceased,
    deceasedDate: values.isDeceased ? blankToNull(values.deceasedDate) : null,
    confirmDuplicate,
  };
}

const STRING_FIELDS = [
  "firstName",
  "lastName",
  "firstNameAlt",
  "lastNameAlt",
  "phonePrimary",
  "phoneSecondary",
  "email",
  "addressLine1",
  "addressLine2",
  "city",
  "postalCode",
  "countryCode",
  "occupation",
  "noiseExposure",
  "smokingStatus",
  "alcoholStatus",
  "insuranceNumber",
  "referringDoctorName",
  "referringDoctorPhone",
  "referringDoctorEmail",
  "referringDoctorLocale",
  "guardianName",
  "guardianRelation",
  "emergencyContactName",
  "emergencyContactPhone",
  "deceasedDate",
  "preferredLocale",
  "birthDate",
] as const satisfies readonly (keyof PatientFormValues)[];

export function partialFormToUpdate(
  values: Partial<PatientFormValues>,
  version: number,
): PatientUpdate {
  const body: PatientUpdate = { version };
  for (const field of STRING_FIELDS) {
    if (!(field in values) || values[field] === undefined) {
      continue;
    }
    const raw = values[field];
    if (typeof raw !== "string") {
      continue;
    }
    if (
      field === "firstName" ||
      field === "lastName" ||
      field === "birthDate"
    ) {
      body[field] = raw.trim();
      continue;
    }
    if (field === "countryCode") {
      body.countryCode = blankToNull(raw)?.toUpperCase() ?? null;
      continue;
    }
    if (field === "deceasedDate") {
      body.deceasedDate = blankToNull(raw);
      continue;
    }
    body[field] = blankToNull(raw);
  }
  if (values.sex !== undefined) {
    body.sex = values.sex;
  }
  if (values.birthDateIsEstimated !== undefined) {
    body.birthDateIsEstimated = values.birthDateIsEstimated;
  }
  if (values.consentSms !== undefined) {
    body.consentSms = values.consentSms;
  }
  if (values.consentEmail !== undefined) {
    body.consentEmail = values.consentEmail;
  }
  if (values.consentTeaching !== undefined) {
    body.consentTeaching = values.consentTeaching;
  }
  if (values.isDeceased !== undefined) {
    body.isDeceased = values.isDeceased;
  }
  return body;
}
