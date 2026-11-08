import { apiFetch } from "@/lib/api/client";
import type {
  CalculationResultRead,
  CalculatorSpecRead,
  PageSchemaCalculatorSpecRead,
} from "@/features/calculators/types/calculator.types";

type Scope = { locale: string; clinicPublicId: string };

function query(
  params: Record<string, string | number | boolean | undefined>,
): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export function fetchCalculators(
  scope: Scope,
  params?: {
    domain?: string;
    interactiveOnly?: boolean;
    limit?: number;
    offset?: number;
  },
): Promise<PageSchemaCalculatorSpecRead> {
  return apiFetch<PageSchemaCalculatorSpecRead>(
    `/api/v1/calculators${query({
      domain: params?.domain,
      interactiveOnly: params?.interactiveOnly ?? true,
      limit: params?.limit ?? 100,
      offset: params?.offset ?? 0,
    })}`,
    scope,
  );
}

export function fetchCalculatorSpec(
  scope: Scope,
  code: string,
): Promise<CalculatorSpecRead> {
  return apiFetch<CalculatorSpecRead>(`/api/v1/calculators/${code}`, scope);
}

export function evaluateCalculator(
  scope: Scope,
  code: string,
  body: {
    inputs: Record<string, string | number | boolean | null | undefined>;
    saveToConsultation?: boolean;
    patientId?: string | null;
    encounterId?: string | null;
  },
): Promise<CalculationResultRead> {
  return apiFetch<CalculationResultRead>(`/api/v1/calculators/${code}`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}
