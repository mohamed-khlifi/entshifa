import type { useTranslations } from "next-intl";
import { z } from "zod";

import { SEX_VALUES } from "../constants";

type PatientTranslator = ReturnType<typeof useTranslations<"patients">>;

export function createPatientFormSchema(t: PatientTranslator) {
  return z
    .object({
      mrn: z.string().max(32),
      firstName: z.string().trim().min(1, t("validation.required")).max(80),
      lastName: z.string().trim().min(1, t("validation.required")).max(80),
      firstNameAlt: z.string().max(80),
      lastNameAlt: z.string().max(80),
      birthDate: z.string().min(1, t("validation.required")),
      birthDateIsEstimated: z.boolean(),
      sex: z.enum(SEX_VALUES),
      preferredLocale: z.string().min(2, t("validation.locale")).max(10),
      phonePrimary: z.string().max(32),
      phoneSecondary: z.string().max(32),
      email: z
        .string()
        .refine(
          (value) =>
            value.trim() === "" || z.string().email().safeParse(value).success,
          t("validation.email"),
        ),
      addressLine1: z.string().max(160),
      addressLine2: z.string().max(160),
      city: z.string().max(80),
      postalCode: z.string().max(20),
      countryCode: z
        .string()
        .refine(
          (value) => value.trim() === "" || /^[A-Za-z]{2}$/.test(value.trim()),
          t("validation.countryCode"),
        ),
      occupation: z.string().max(120),
      noiseExposure: z.string().max(40),
      smokingStatus: z.string().max(30),
      alcoholStatus: z.string().max(30),
      insuranceNumber: z.string().max(60),
      referringDoctorName: z.string().max(160),
      referringDoctorPhone: z.string().max(32),
      referringDoctorEmail: z
        .string()
        .refine(
          (value) =>
            value.trim() === "" || z.string().email().safeParse(value).success,
          t("validation.email"),
        ),
      referringDoctorLocale: z.string().max(10),
      guardianName: z.string().max(160),
      guardianRelation: z.string().max(40),
      emergencyContactName: z.string().max(160),
      emergencyContactPhone: z.string().max(32),
      consentSms: z.boolean(),
      consentEmail: z.boolean(),
      consentTeaching: z.boolean(),
      isDeceased: z.boolean(),
      deceasedDate: z.string(),
    })
    .superRefine((value, ctx) => {
      if (value.deceasedDate.trim() !== "" && !value.isDeceased) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["deceasedDate"],
          message: t("validation.deceased"),
        });
      }
      if (
        value.referringDoctorLocale.trim() !== "" &&
        value.referringDoctorLocale.trim().length < 2
      ) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["referringDoctorLocale"],
          message: t("validation.locale"),
        });
      }
    });
}

export type PatientFormValues = z.infer<
  ReturnType<typeof createPatientFormSchema>
>;

export const emptyPatientFormValues: PatientFormValues = {
  mrn: "",
  firstName: "",
  lastName: "",
  firstNameAlt: "",
  lastNameAlt: "",
  birthDate: "",
  birthDateIsEstimated: false,
  sex: "unknown",
  preferredLocale: "fr",
  phonePrimary: "",
  phoneSecondary: "",
  email: "",
  addressLine1: "",
  addressLine2: "",
  city: "",
  postalCode: "",
  countryCode: "",
  occupation: "",
  noiseExposure: "",
  smokingStatus: "",
  alcoholStatus: "",
  insuranceNumber: "",
  referringDoctorName: "",
  referringDoctorPhone: "",
  referringDoctorEmail: "",
  referringDoctorLocale: "",
  guardianName: "",
  guardianRelation: "",
  emergencyContactName: "",
  emergencyContactPhone: "",
  consentSms: false,
  consentEmail: false,
  consentTeaching: false,
  isDeceased: false,
  deceasedDate: "",
};
