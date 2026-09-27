"use client";

import { useTranslations } from "next-intl";

import { uploadPercent } from "../utils/media-kind";
import { Button } from "@/components/ui/button";
import { testIdProps, testIds } from "@/lib/test/test-id";

export type UploadPhase =
  "idle" | "requesting" | "uploading" | "confirming" | "failed";

type AttachmentUploadProgressProps = {
  phase: UploadPhase;
  loaded: number;
  total: number;
  loadedLabel: string;
  totalLabel: string;
  onRetry: () => void;
};

export function AttachmentUploadProgress({
  phase,
  loaded,
  total,
  loadedLabel,
  totalLabel,
  onRetry,
}: AttachmentUploadProgressProps) {
  const t = useTranslations("attachments");
  if (phase === "idle") {
    return null;
  }
  const percent = phase === "confirming" ? 100 : uploadPercent(loaded, total);
  const failed = phase === "failed";

  return (
    <div
      className="space-y-2"
      {...testIdProps(testIds.attachments.uploadProgress)}
    >
      <div
        className="h-2 overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
      >
        <div
          className="h-full rounded-full bg-primary transition-[width]"
          style={{ width: `${percent}%` }}
        />
      </div>
      <p className="text-sm text-muted-foreground">
        {t("upload.progress", {
          percent,
          loaded: loadedLabel,
          total: totalLabel,
        })}
      </p>
      {failed ? (
        <div className="flex flex-wrap items-center gap-3">
          <p
            className="text-sm text-destructive"
            role="alert"
            {...testIdProps(testIds.attachments.uploadError)}
          >
            {t("upload.errors.storage")}
          </p>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={onRetry}
            {...testIdProps(testIds.attachments.uploadRetry)}
          >
            {t("upload.retry")}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
