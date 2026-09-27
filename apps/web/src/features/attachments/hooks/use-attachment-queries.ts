"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import {
  confirmAttachmentUpload,
  fetchAttachmentDownloadUrl,
  fetchAttachments,
  requestAttachmentUploadUrl,
  type AttachmentListParams,
} from "../api/attachments.api";
import { putFileWithRetry, putPresignedFile } from "../utils/direct-upload";
import { queryKeys } from "@/lib/api/query-keys";
import type { AttachmentUploadUrlRequest } from "@/lib/api/generated";
import { useSession } from "@/providers/session-provider";

const PENDING_STATUSES = new Set(["pending", "processing"]);

function useScope() {
  const locale = useLocale();
  const { session } = useSession();
  return {
    locale,
    clinicPublicId: session?.clinicPublicId ?? "",
    enabled: Boolean(session?.clinicPublicId),
  };
}

export function useAttachmentsQuery(filters: AttachmentListParams) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.attachments.list(filters),
    queryFn: () =>
      fetchAttachments(
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        filters,
      ),
    enabled: scope.enabled && filters.patientPublicId.length > 0,
    staleTime: 15_000,
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      const waiting = items.some((item) =>
        PENDING_STATUSES.has(item.processingStatus),
      );
      return waiting ? 4_000 : false;
    },
  });
}

export function useAttachmentDownloadQuery(
  publicId: string,
  variant: string | undefined,
  enabled: boolean,
) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.attachments.download(publicId, variant),
    queryFn: () =>
      fetchAttachmentDownloadUrl(
        publicId,
        scope.locale,
        scope.clinicPublicId,
        variant,
      ),
    enabled: scope.enabled && enabled && publicId.length > 0,
    staleTime: 30_000,
  });
}

export type UploadAttachmentInput = {
  file: File;
  body: AttachmentUploadUrlRequest;
  onProgress: (loaded: number, total: number) => void;
};

export function useUploadAttachmentMutation() {
  const t = useTranslations("attachments");
  const scope = useScope();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: UploadAttachmentInput) => {
      const ticket = await requestAttachmentUploadUrl(
        input.body,
        scope.locale,
        scope.clinicPublicId,
      );
      await putFileWithRetry(() =>
        putPresignedFile(ticket.upload, input.file, input.onProgress),
      );
      return confirmAttachmentUpload(
        { uploadToken: ticket.uploadToken },
        scope.locale,
        scope.clinicPublicId,
      );
    },
    onSuccess: async () => {
      toast.success(t("upload.toast.saved"));
      await queryClient.invalidateQueries({
        queryKey: queryKeys.attachments.all,
      });
    },
    onError: () => {
      toast.error(t("upload.toast.failed"));
    },
  });
}
