import type { useTranslations } from "next-intl";
import { z } from "zod";

import { PRESCRIPTION_ROUTES } from "../constants";

type PrescriptionT = ReturnType<typeof useTranslations<"prescriptions">>;

const decimal = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;

export function createPrescriptionFormSchema(t: PrescriptionT) {
  const item = z
    .object({
      key: z.string().min(1),
      formularyEntryPublicId: z.string(),
      freeTextName: z.string(),
      label: z.string(),
      doseAmount: z.string(),
      doseUnit: z.string(),
      route: z.enum(PRESCRIPTION_ROUTES),
      frequencyPerDay: z.string().regex(/^\d+$/, t("validation.range")),
      durationDays: z.string().regex(/^\d+$/, t("validation.range")),
      quantity: z.string(),
      instructionsText: z.string(),
      isRenewable: z.boolean(),
      substitutionAllowed: z.boolean(),
      calculateFromFormulary: z.boolean(),
      indicationCode: z.string(),
      useFormularyTaper: z.boolean(),
      taperStartMg: z.string(),
      taperStepMg: z.string(),
      taperDaysPerStep: z.string(),
      taperMinimumMg: z.string(),
      allergyOverride: z.string(),
      doseOverride: z.string(),
    })
    .superRefine((value, context) => {
      const hasFormulary = value.formularyEntryPublicId.trim().length === 26;
      const hasText = value.freeTextName.trim().length > 0;
      if (hasFormulary === hasText) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: t("validation.identity"),
          path: ["freeTextName"],
        });
      }
      if (
        !value.calculateFromFormulary &&
        !decimal.test(value.doseAmount.trim())
      ) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: t("validation.dose"),
          path: ["doseAmount"],
        });
      }
      const taperParts = [
        value.taperStartMg,
        value.taperStepMg,
        value.taperDaysPerStep,
        value.taperMinimumMg,
      ];
      const taperStarted = taperParts.some((part) => part.trim().length > 0);
      if (taperStarted && value.useFormularyTaper) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: t("validation.taper"),
          path: ["taperStartMg"],
        });
      }
      if (taperStarted && taperParts.some((part) => part.trim().length === 0)) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: t("validation.taper"),
          path: ["taperStartMg"],
        });
      }
    });

  return z.object({
    isPediatric: z.boolean(),
    weightKg: z.string(),
    notes: z.string(),
    items: z.array(item).min(1, t("validation.item")),
  });
}

export function createTemplateCodeSchema(t: PrescriptionT) {
  return z.object({
    code: z
      .string()
      .trim()
      .regex(/^[a-z0-9_]+$/, t("validation.code"))
      .min(1, t("validation.required"))
      .max(40),
  });
}
