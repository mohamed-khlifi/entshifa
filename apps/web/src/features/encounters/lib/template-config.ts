import { z } from "zod";

const historyFieldSchema = z.object({
  id: z.string().min(1),
  labelKey: z.string().min(1),
  fieldType: z.enum(["text", "boolean", "select", "multiselect", "number"]),
  options: z.array(z.string()).nullable().optional(),
  required: z.boolean().optional().default(false),
});

const templateConfigSchema = z.object({
  historyFields: z.array(historyFieldSchema).optional().default([]),
  examSections: z.array(z.string()).optional().default([]),
  suggestedInstruments: z.array(z.string()).optional().default([]),
  suggestedTests: z.array(z.string()).optional().default([]),
  suggestedDocuments: z.array(z.string()).optional().default([]),
  favoriteDiagnoses: z.array(z.string()).optional().default([]),
  defaultFollowUpDays: z.number().int().positive().nullable().optional(),
});

export type HistoryFieldConfig = z.infer<typeof historyFieldSchema>;
export type TemplateConfig = Omit<
  z.infer<typeof templateConfigSchema>,
  "defaultFollowUpDays"
> & {
  defaultFollowUpDays: number | null;
};

export const EMPTY_TEMPLATE_CONFIG: TemplateConfig = {
  historyFields: [],
  examSections: [],
  suggestedInstruments: [],
  suggestedTests: [],
  suggestedDocuments: [],
  favoriteDiagnoses: [],
  defaultFollowUpDays: null,
};

export function parseTemplateConfig(config: unknown): TemplateConfig {
  const parsed = templateConfigSchema.safeParse(config);
  if (!parsed.success) {
    return EMPTY_TEMPLATE_CONFIG;
  }
  return {
    ...parsed.data,
    defaultFollowUpDays: parsed.data.defaultFollowUpDays ?? null,
  };
}
