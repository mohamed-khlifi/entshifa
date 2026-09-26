import { z } from "zod";

import { LATERALITY_VALUES } from "@/components/forms/LateralityField";

export function createUiKitDemoSchema(messages: {
  lastNameRequired: string;
  weightRequired: string;
  sexRequired: string;
  birthDateRequired: string;
  sideRequired: string;
  diagnosisRequired: string;
  painRequired: string;
}) {
  return z.object({
    lastName: z.string().min(1, { message: messages.lastNameRequired }),
    weightKg: z
      .number({ required_error: messages.weightRequired })
      .min(0.5)
      .max(300),
    sex: z.string().min(1, { message: messages.sexRequired }),
    birthDate: z.string().min(1, { message: messages.birthDateRequired }),
    side: z.enum(LATERALITY_VALUES, { required_error: messages.sideRequired }),
    diagnosis: z.string().min(1, { message: messages.diagnosisRequired }),
    painScore: z
      .number({ required_error: messages.painRequired })
      .min(0)
      .max(10),
  });
}

export type UiKitDemoValues = z.infer<ReturnType<typeof createUiKitDemoSchema>>;
