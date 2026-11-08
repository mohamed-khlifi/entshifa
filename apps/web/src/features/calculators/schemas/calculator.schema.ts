import { z } from "zod";

import type { CalculatorInputFieldRead } from "@/features/calculators/types/calculator.types";

export function buildCalculatorFormSchema(fields: CalculatorInputFieldRead[]) {
  const shape: Record<string, z.ZodTypeAny> = {};
  for (const field of fields) {
    let schema: z.ZodTypeAny;
    if (field.kind === "boolean") {
      schema = field.required ? z.boolean() : z.boolean().optional();
    } else if (field.kind === "date") {
      schema = field.required
        ? z.string().min(1, "forms.validation.required")
        : z.string().optional();
    } else if (field.kind === "select") {
      const values = field.options.map((option) => option.value);
      schema = field.required
        ? z.enum(values as [string, ...string[]])
        : z.enum(values as [string, ...string[]]).optional();
    } else {
      const base =
        field.kind === "integer" ? z.coerce.number().int() : z.coerce.number();
      if (field.minValue !== null && field.minValue !== undefined) {
        const min = Number(field.minValue);
        if (!Number.isNaN(min)) {
          base.min(min, "forms.validation.min");
        }
      }
      if (field.maxValue !== null && field.maxValue !== undefined) {
        const max = Number(field.maxValue);
        if (!Number.isNaN(max)) {
          base.max(max, "forms.validation.max");
        }
      }
      schema = field.required ? base : base.optional();
    }
    shape[field.name] = schema;
  }
  return z.object(shape);
}

export function defaultValuesFromSpec(
  fields: CalculatorInputFieldRead[],
): Record<string, string | boolean> {
  const defaults: Record<string, string | boolean> = {};
  for (const field of fields) {
    if (field.defaultValue) {
      if (field.kind === "boolean") {
        defaults[field.name] = field.defaultValue === "true";
      } else {
        defaults[field.name] = field.defaultValue;
      }
    } else if (field.kind === "boolean") {
      defaults[field.name] = false;
    }
  }
  return defaults;
}
