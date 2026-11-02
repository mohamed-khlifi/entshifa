import { z } from "zod";

import {
  BONE_FREQUENCIES_HZ,
  MAX_LEVEL_DB,
  MIN_LEVEL_DB,
  RELIABILITY_VALUES,
  STANDARD_FREQUENCIES_HZ,
  TEST_METHODS,
  TRANSDUCERS,
} from "../constants";

const ALL_FREQ = [
  ...STANDARD_FREQUENCIES_HZ,
  10000,
  12500,
  14000,
  16000,
] as const;

export const thresholdCellSchema = z.object({
  levelDb: z.number().int().min(MIN_LEVEL_DB).max(MAX_LEVEL_DB).nullable(),
  isNoResponse: z.boolean(),
});

export const thresholdInputSchema = z
  .object({
    ear: z.enum(["right", "left"]),
    conduction: z.enum(["air", "bone"]),
    frequencyHz: z.number().int(),
    levelDb: z.number().int().min(MIN_LEVEL_DB).max(MAX_LEVEL_DB).nullable(),
    isMasked: z.boolean(),
    isNoResponse: z.boolean(),
  })
  .superRefine((value, ctx) => {
    if (!(ALL_FREQ as readonly number[]).includes(value.frequencyHz)) {
      ctx.addIssue({
        code: "custom",
        message: "audiology.validation.frequency",
      });
    }
    if (
      value.conduction === "bone" &&
      !(BONE_FREQUENCIES_HZ as readonly number[]).includes(value.frequencyHz)
    ) {
      ctx.addIssue({
        code: "custom",
        message: "audiology.validation.boneFrequency",
      });
    }
    if (!value.isNoResponse && value.levelDb === null) {
      ctx.addIssue({ code: "custom", message: "audiology.validation.level" });
    }
  });

export const audiogramDraftSchema = z.object({
  performedAt: z.string().min(1, "audiology.validation.performedAt"),
  transducer: z.enum(TRANSDUCERS),
  method: z.enum(TEST_METHODS),
  reliability: z.enum(RELIABILITY_VALUES),
  equipment: z.string(),
  calibrationDate: z.string(),
  interpretationText: z.string(),
  isBaseline: z.boolean(),
});
