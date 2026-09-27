"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import {
  createDocument,
  createDocumentTemplate,
  documentDownloadUrl,
  fetchDocumentTemplate,
  fetchDocumentTemplates,
  fetchPatientDocuments,
  finalizeDocument,
  previewDocument,
  previewTemplate,
  publishTemplateVersion,
} from "../api/documents.api";
import { documentErrorText } from "../lib/errors";
import { queryKeys } from "@/lib/api/query-keys";
import type {
  DocumentCreate,
  DocumentTemplateCreate,
  DocumentTemplatePreview,
  DocumentTemplateVersionCreate,
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

export function useDocumentTemplatesQuery() {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.documents.templates(),
    queryFn: () => fetchDocumentTemplates(scope),
    enabled: scope.enabled,
    staleTime: 30_000,
  });
}

export function useDocumentTemplateQuery(templateId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.documents.template(templateId),
    queryFn: () => fetchDocumentTemplate(scope, templateId),
    enabled: scope.enabled && templateId.length > 0,
    staleTime: 15_000,
  });
}

export function usePatientDocumentsQuery(patientPublicId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.documents.patient(patientPublicId),
    queryFn: () => fetchPatientDocuments(scope, patientPublicId),
    enabled: scope.enabled && patientPublicId.length > 0,
    staleTime: 15_000,
  });
}

export function useDocumentPreviewQuery(documentId: string, enabled: boolean) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.documents.preview(documentId),
    queryFn: () => previewDocument(scope, documentId),
    enabled: scope.enabled && enabled && documentId.length > 0,
    staleTime: 0,
  });
}

export function useCreateDocumentMutation(patientPublicId: string) {
  const scope = useScope();
  const client = useQueryClient();
  const tErrors = useTranslations("errors");
  return useMutation({
    mutationFn: (body: DocumentCreate) => createDocument(scope, body),
    onSuccess: async () => {
      await client.invalidateQueries({
        queryKey: queryKeys.documents.patient(patientPublicId),
      });
    },
    onError: (error) => {
      toast.error(documentErrorText(tErrors, error));
    },
  });
}

export function useFinalizeDocumentMutation(patientPublicId: string) {
  const scope = useScope();
  const client = useQueryClient();
  const t = useTranslations("documents");
  const tErrors = useTranslations("errors");
  return useMutation({
    mutationFn: (documentId: string) => finalizeDocument(scope, documentId, {}),
    onSuccess: async (_data, documentId) => {
      toast.success(t("list.finalize"));
      await client.invalidateQueries({
        queryKey: queryKeys.documents.patient(patientPublicId),
      });
      await client.invalidateQueries({
        queryKey: queryKeys.documents.preview(documentId),
      });
    },
    onError: (error) => {
      toast.error(documentErrorText(tErrors, error));
    },
  });
}

export function useTemplatePreviewMutation() {
  const scope = useScope();
  const tErrors = useTranslations("errors");
  return useMutation({
    mutationFn: (body: DocumentTemplatePreview) => previewTemplate(scope, body),
    onError: (error) => {
      toast.error(documentErrorText(tErrors, error));
    },
  });
}

export function usePublishTemplateVersionMutation(templateId: string) {
  const scope = useScope();
  const client = useQueryClient();
  const t = useTranslations("documents");
  const tErrors = useTranslations("errors");
  return useMutation({
    mutationFn: (body: DocumentTemplateVersionCreate) =>
      publishTemplateVersion(scope, templateId, body),
    onSuccess: async () => {
      toast.success(t("editor.saved"));
      await client.invalidateQueries({
        queryKey: queryKeys.documents.template(templateId),
      });
    },
    onError: (error) => {
      toast.error(documentErrorText(tErrors, error));
    },
  });
}

export function useCopyTemplateMutation() {
  const scope = useScope();
  const client = useQueryClient();
  const tErrors = useTranslations("errors");
  return useMutation({
    mutationFn: (body: DocumentTemplateCreate) =>
      createDocumentTemplate(scope, body),
    onSuccess: async () => {
      await client.invalidateQueries({
        queryKey: queryKeys.documents.templates(),
      });
    },
    onError: (error) => {
      toast.error(documentErrorText(tErrors, error));
    },
  });
}

export function useDocumentDownload() {
  const scope = useScope();
  return (documentId: string) => documentDownloadUrl(scope, documentId);
}
