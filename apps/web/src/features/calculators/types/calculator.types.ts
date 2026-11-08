export type CalculatorInputOptionRead = {
  value: string;
  labelKey: string;
};

export type CalculatorInputFieldRead = {
  name: string;
  kind: string;
  required: boolean;
  labelKey: string;
  unit?: string | null;
  minValue?: string | null;
  maxValue?: string | null;
  defaultValue?: string | null;
  options: CalculatorInputOptionRead[];
};

export type CalculatorSpecRead = {
  code: string;
  domain: string;
  version: string;
  reference: string;
  unit?: string | null;
  formula: string;
  interactive: boolean;
  inputs: CalculatorInputFieldRead[];
};

export type CalculationFlagRead = {
  code: string;
  detail: Record<string, string>;
};

export type CalculationResultRead = {
  code: string;
  value: string;
  unit?: string | null;
  inputs: Record<string, string>;
  formula: string;
  version: string;
  reference: string;
  flags: CalculationFlagRead[];
  savedResultId?: string | null;
  computedAt?: string | null;
};

export type PageSchemaCalculatorSpecRead = {
  items: CalculatorSpecRead[];
  page: {
    total: number;
    limit: number;
    offset: number;
    nextCursor: string | null;
  };
};
