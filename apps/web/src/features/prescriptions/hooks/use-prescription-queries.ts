"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import {
  calculatePediatricDose,
  cancelPrescription,
  checkPrescriptionSafety,
  createPrescription,
  createPrescriptionTemplate,
  generatePrescriptionTaper,
  issuePrescription,
  listFormulary,
  listPatientEncounters,
  listPatientPrescriptions,
  listPrescriptionTemplates,
  searchDrugs,
  updatePrescription,
} from "../api/prescriptions.api";
import { prescriptionErrorText } from "../lib/errors";
import { queryKeys } from "@/lib/api/query-keys";
import type {
  PediatricDoseRequest,
  PrescriptionCreate,
  PrescriptionTemplateCreate,
  PrescriptionUpdate,
  SafetyAlertRead,
  SafetyCheckRequest,
  TaperRequest,
} from "@/lib/api/generated";
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

export function useFormularyQuery(q: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.prescriptions.formulary(q),
    queryFn: () => listFormulary(scope, q),
    enabled: scope.enabled,
    staleTime: 60_000,
  });
}

export function useDrugSearchQuery(q: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.prescriptions.drugs(q),
    queryFn: () => searchDrugs(scope, q),
    enabled: scope.enabled && q.trim().length > 0,
    staleTime: 60_000,
  });
}

export function usePrescriptionTemplatesQuery() {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.prescriptions.templates(),
    queryFn: () => listPrescriptionTemplates(scope),
    enabled: scope.enabled,
    staleTime: 30_000,
  });
}

export function usePatientPrescriptionsQuery(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.prescriptions.patient(patientId),
    queryFn: () => listPatientPrescriptions(scope, patientId),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: 15_000,
  });
}

export function usePatientEncountersQuery(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.encounters.patient(patientId),
    queryFn: () => listPatientEncounters(scope, patientId),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: 15_000,
  });
}

function useInvalidatePatient(patientId: string) {
  const client = useQueryClient();
  return async (prescriptionId?: string) => {
    await client.invalidateQueries({
      queryKey: queryKeys.prescriptions.patient(patientId),
    });
    await client.invalidateQueries({
      queryKey: queryKeys.patients.detail(patientId),
    });
    if (prescriptionId) {
      await client.invalidateQueries({
        queryKey: queryKeys.prescriptions.detail(prescriptionId),
      });
    }
  };
}

export function useCreatePrescriptionMutation(patientId: string) {
  const scope = useScope();
  const invalidate = useInvalidatePatient(patientId);
  const tErrors = useTranslations("errors");
  return useMutation({
    mutationFn: (input: { body: PrescriptionCreate; idempotencyKey: string }) =>
      createPrescription(scope, patientId, input.body, input.idempotencyKey),
    onSuccess: async (saved) => {
      await invalidate(saved.publicId);
    },
    onError: (error) => {
      toast.error(prescriptionErrorText(tErrors, error));
    },
  });
}

export function useUpdatePrescriptionMutation(patientId: string) {
  const scope = useScope();
  const invalidate = useInvalidatePatient(patientId);
  const tErrors = useTranslations("errors");
  return useMutation({
    mutationFn: (input: { prescriptionId: string; body: PrescriptionUpdate }) =>
      updatePrescription(scope, input.prescriptionId, input.body),
    onSuccess: async (saved) => {
      await invalidate(saved.publicId);
    },
    onError: (error) => {
      toast.error(prescriptionErrorText(tErrors, error));
    },
  });
}

export function useIssuePrescriptionMutation(patientId: string) {
  const scope = useScope();
  const invalidate = useInvalidatePatient(patientId);
  const tErrors = useTranslations("errors");
  return useMutation({
    mutationFn: (prescriptionId: string) =>
      issuePrescription(scope, prescriptionId),
    onSuccess: async (saved) => {
      await invalidate(saved.publicId);
    },
    onError: (error) => {
      toast.error(prescriptionErrorText(tErrors, error));
    },
  });
}

export function useCancelPrescriptionMutation(patientId: string) {
  const scope = useScope();
  const invalidate = useInvalidatePatient(patientId);
  const tErrors = useTranslations("errors");
  return useMutation({
    mutationFn: (prescriptionId: string) =>
      cancelPrescription(scope, prescriptionId),
    onSuccess: async (saved) => {
      await invalidate(saved.publicId);
    },
    onError: (error) => {
      toast.error(prescriptionErrorText(tErrors, error));
    },
  });
}

export function useCreateTemplateMutation() {
  const scope = useScope();
  const client = useQueryClient();
  const tErrors = useTranslations("errors");
  return useMutation({
    mutationFn: (body: PrescriptionTemplateCreate) =>
      createPrescriptionTemplate(scope, body),
    onSuccess: async () => {
      await client.invalidateQueries({
        queryKey: queryKeys.prescriptions.templates(),
      });
    },
    onError: (error) => {
      toast.error(prescriptionErrorText(tErrors, error));
    },
  });
}

export function useCalculateDoseMutation(patientId: string) {
  const scope = useScope();
  const tErrors = useTranslations("errors");
  return useMutation({
    mutationFn: (body: PediatricDoseRequest) =>
      calculatePediatricDose(scope, patientId, body),
    onError: (error) => {
      toast.error(prescriptionErrorText(tErrors, error));
    },
  });
}

export function useGenerateTaperMutation(patientId: string) {
  const scope = useScope();
  const tErrors = useTranslations("errors");
  return useMutation({
    mutationFn: (body: TaperRequest) =>
      generatePrescriptionTaper(scope, patientId, body),
    onError: (error) => {
      toast.error(prescriptionErrorText(tErrors, error));
    },
  });
}

export function useLiveSafety(
  patientId: string,
  body: SafetyCheckRequest | null,
) {
  const scope = useScope();
  const [alerts, setAlerts] = useState<SafetyAlertRead[]>([]);
  const bodyRef = useRef(body);
  bodyRef.current = body;
  const signature = body == null ? "" : JSON.stringify(body);
  const { enabled, locale, clinicPublicId } = scope;

  useEffect(() => {
    const current = bodyRef.current;
    if (!enabled || current == null) {
      setAlerts([]);
      return;
    }
    const handle = window.setTimeout(() => {
      void checkPrescriptionSafety(
        { locale, clinicPublicId },
        patientId,
        current,
      )
        .then(setAlerts)
        .catch(() => setAlerts([]));
    }, 400);
    return () => window.clearTimeout(handle);
  }, [patientId, enabled, locale, clinicPublicId, signature]);

  return alerts;
}
