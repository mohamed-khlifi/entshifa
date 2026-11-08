"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useLocale } from "next-intl";

import {
  evaluateCalculator,
  fetchCalculatorSpec,
  fetchCalculators,
} from "@/features/calculators/api/calculators.api";
import { queryKeys } from "@/lib/api/query-keys";
import { useSession } from "@/providers/session-provider";

function useScope() {
  const locale = useLocale();
  const { session } = useSession();
  return {
    locale,
    clinicPublicId: session?.clinicPublicId ?? "",
    enabled: Boolean(session?.clinicPublicId),
  };
}

export function useCalculatorsList(domain?: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.calculators.list({ domain }),
    queryFn: () =>
      fetchCalculators(
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        { domain, interactiveOnly: true },
      ),
    staleTime: 60 * 60 * 1000,
    enabled: scope.enabled,
  });
}

export function useCalculatorSpec(code: string | undefined) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.calculators.detail(code ?? ""),
    queryFn: () =>
      fetchCalculatorSpec(
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        code ?? "",
      ),
    enabled: scope.enabled && Boolean(code),
    staleTime: 60 * 60 * 1000,
  });
}

export function useEvaluateCalculator(code: string) {
  const scope = useScope();
  return useMutation({
    mutationFn: (body: Parameters<typeof evaluateCalculator>[2]) =>
      evaluateCalculator(
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        code,
        body,
      ),
  });
}
