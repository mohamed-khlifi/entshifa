import { describe, expect, it } from "vitest";

import {
  buildCalculatorFormSchema,
  defaultValuesFromSpec,
} from "@/features/calculators/schemas/calculator.schema";
import type { CalculatorInputFieldRead } from "@/features/calculators/types/calculator.types";

const sampleFields: CalculatorInputFieldRead[] = [
  {
    name: "percent",
    kind: "decimal",
    required: true,
    labelKey: "calculators.fields.percent",
    unit: "%",
    minValue: "0",
    maxValue: "100",
    defaultValue: null,
    options: [],
  },
  {
    name: "grade",
    kind: "select",
    required: true,
    labelKey: "calculators.fields.grade",
    unit: null,
    minValue: null,
    maxValue: null,
    defaultValue: "1",
    options: [
      { value: "0", labelKey: "calculators.options.zero" },
      { value: "1", labelKey: "calculators.options.one" },
    ],
  },
];

describe("buildCalculatorFormSchema", () => {
  it("parses numeric and select fields", () => {
    const schema = buildCalculatorFormSchema(sampleFields);
    const parsed = schema.parse({ percent: "42", grade: "1" });
    expect(parsed.percent).toBe(42);
    expect(parsed.grade).toBe("1");
  });
});

describe("defaultValuesFromSpec", () => {
  it("hydrates boolean false and string defaults", () => {
    const defaults = defaultValuesFromSpec(sampleFields);
    expect(defaults.grade).toBe("1");
    expect(defaults.percent).toBeUndefined();
  });
});
