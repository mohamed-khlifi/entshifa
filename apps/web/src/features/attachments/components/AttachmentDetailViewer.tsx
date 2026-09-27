"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect } from "react";

import { useCurrentClinicQuery } from "@/features/clinics";
import { fetchAttachmentDownloadUrl } from "../api/attachments.api";
import { useAttachmentDownloadQuery } from "../hooks/use-attachment-queries";
import {
  categoryLabel,
  consentLabel,
  lateralityLabel,
  processingLabel,
} from "../labels";
import { mediaKind, viewerVariant } from "../utils/media-kind";
import { Button } from "@/components/ui/button";
import type { AttachmentRead } from "@/lib/api/generated";
import { formatDateTimeInTimeZone } from "@/lib/i18n/format";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

type AttachmentDetailViewerProps = {
  item: AttachmentRead;
  onClose: () => void;
};

export function AttachmentDetailViewer({
  item,
  onClose,
}: AttachmentDetailViewerProps) {
  const t = useTranslations("attachments");
  const locale = useLocale();
  const { session } = useSession();
  const clinic = useCurrentClinicQuery();
  const timeZone = clinic.data?.timezone ?? "UTC";
  const kind = mediaKind(item.category, item.contentType);
  const variant = kind === "image" ? viewerVariant(item.variants) : undefined;
  const media = useAttachmentDownloadQuery(
    item.publicId,
    variant,
    kind === "image" || kind === "video" || kind === "audio",
  );
  const url = media.data?.download.url;
  const when = item.capturedAt ?? item.createdAt;

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const openOriginal = async () => {
    if (!session?.clinicPublicId) {
      return;
    }
    const download = await fetchAttachmentDownloadUrl(
      item.publicId,
      locale,
      session.clinicPublicId,
    );
    window.open(download.download.url, "_blank", "noopener,noreferrer");
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-foreground/40 p-4 sm:items-center"
      role="presentation"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="attachment-viewer-title"
        className="max-h-[90vh] w-full max-w-4xl overflow-auto rounded-xl border border-border bg-card p-5 shadow-[var(--shadow-soft)]"
        onClick={(event) => event.stopPropagation()}
        {...testIdProps(testIds.attachments.viewer)}
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 id="attachment-viewer-title" className="text-lg font-semibold">
              {t("viewer.title")}
            </h2>
            <p className="text-sm text-muted-foreground">{item.filename}</p>
          </div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={onClose}
            {...testIdProps(testIds.attachments.viewerClose)}
          >
            {t("viewer.close")}
          </Button>
        </div>
        <dl
          className="mb-4 grid gap-2 text-sm sm:grid-cols-2"
          {...testIdProps(testIds.attachments.viewerMeta)}
        >
          <div>
            <dt className="text-muted-foreground">{t("upload.category")}</dt>
            <dd>{categoryLabel(t, item.category)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("upload.laterality")}</dt>
            <dd>{lateralityLabel(t, item.laterality)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("viewer.bodySite")}</dt>
            <dd>{item.bodySite?.display ?? t("gallery.noBodySite")}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("viewer.capturedAt")}</dt>
            <dd>
              {when
                ? formatDateTimeInTimeZone(when, timeZone, locale)
                : t("gallery.noDate")}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("viewer.consent")}</dt>
            <dd>{consentLabel(t, item.isConsentedForTeaching)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("viewer.status")}</dt>
            <dd>{processingLabel(t, item.processingStatus)}</dd>
          </div>
        </dl>
        {item.caption ? <p className="mb-4 text-sm">{item.caption}</p> : null}
        <div dir="ltr" className="overflow-hidden rounded-lg bg-muted/40">
          {kind === "image" && url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={url}
              alt={item.caption || item.filename}
              className="max-h-[60vh] w-full object-contain [transform:none]"
              {...testIdProps(testIds.attachments.viewerImage)}
            />
          ) : null}
          {kind === "video" && url ? (
            <video
              src={url}
              controls
              className="max-h-[60vh] w-full [transform:none]"
              {...testIdProps(testIds.attachments.viewerImage)}
            >
              {t("viewer.video")}
            </video>
          ) : null}
          {kind === "audio" && url ? (
            <audio src={url} controls className="w-full p-4">
              {t("viewer.audio")}
            </audio>
          ) : null}
        </div>
        {kind === "document" || !url ? (
          <Button
            type="button"
            className="mt-4"
            onClick={() => void openOriginal()}
            {...testIdProps(testIds.attachments.viewerLoad)}
          >
            {t("viewer.download")}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
