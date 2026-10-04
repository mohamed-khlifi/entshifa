import { z } from "zod";

import { PLAN_KINDS } from "../lib/plan-items";

export const cockpitFormSchema = z.object({
  assessmentNote: z.string().max(20_000),
  complaintSearch: z.string().max(80),
  course: z.enum(["", "constant", "intermittent", "progressive", "improving"]),
  historyNote: z.string().max(20_000),
  impact: z.string().max(500),
  laterality: z.enum(["", "right", "left", "bilateral", "alternating"]),
  onset: z.string().max(60),
  planDraftDetail: z.string().max(500),
  planDraftKind: z.enum(PLAN_KINDS),
  planNote: z.string().max(20_000),
  previousConsultations: z.string().max(4_000),
  previousTreatments: z.string().max(4_000),
  relievingFactors: z.string().max(500),
  severity: z.number().int().min(0).max(10).nullable(),
  templateAnswers: z.record(
    z.string(),
    z.union([z.string(), z.number(), z.boolean(), z.array(z.string())]),
  ),
  triggers: z.string().max(500),
});

export type CockpitFormValues = z.infer<typeof cockpitFormSchema>;

export const cockpitDefaultValues: CockpitFormValues = {
  assessmentNote: "",
  complaintSearch: "",
  course: "",
  historyNote: "",
  impact: "",
  laterality: "",
  onset: "",
  planDraftDetail: "",
  planDraftKind: "medication",
  planNote: "",
  previousConsultations: "",
  previousTreatments: "",
  relievingFactors: "",
  severity: null,
  templateAnswers: {},
  triggers: "",
};
