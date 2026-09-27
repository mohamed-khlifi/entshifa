"use client";

import { useLocale, useTranslations } from "next-intl";

import { useCurrentClinicQuery } from "@/features/clinics";
import { useAttachmentDownloadQuery } from "../hooks/use-attachment-queries";
import {
  categoryLabel,
  consentLabel,
  lateralityLabel,
  processingLabel,
} from "../labels";
import { listVariant, mediaKind } from "../utils/media-kind";
import type { AttachmentRead } from "@/lib/api/generated";
import { formatDateTimeInTimeZone } from "@/lib/i18n/format";
import { publicIdTestId, testIdProps } from "@/lib/test/test-id";

type AttachmentCardProps = {
  item: AttachmentRead;
  onOpen: (item: AttachmentRead) => void;
};

export function AttachmentCard({ item, onOpen }: AttachmentCardProps) {
  const t = useTranslations("attachments");
  const locale = useLocale();
  const clinic = useCurrentClinicQuery();
  const timeZone = clinic.data?.timezone ?? "UTC";
  const kind = mediaKind(item.category, item.contentType);
  const variant = kind === "image" ? listVariant(item.variants) : undefined;
  const download = useAttachmentDownloadQuery(
    item.publicId,
    variant,
    kind === "image" && variant !== undefined,
  );
  const when = item.capturedAt ?? item.createdAt;
  const imageUrl = download.data?.download.url;

  return (
    <button
      type="button"
      className="flex flex-col overflow-hidden rounded-xl border border-border bg-card text-start shadow-[var(--shadow-soft)] transition-colors hover:border-primary/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      onClick={() => onOpen(item)}
      {...testIdProps(publicIdTestId("attachments.card", item.publicId))}
    >
      <div
        className="flex h-36 items-center justify-center bg-muted/50"
        dir="ltr"
      >
        {imageUrl ? (
          // Pre-signed clinical photo; never mirrored in RTL.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imageUrl}
            alt={item.caption || item.filename}
            className="h-full w-full object-contain [transform:none]"
          />
        ) : (
          <span className="px-3 text-center text-xs font-medium text-muted-foreground">
            {categoryLabel(t, item.category)}
          </span>
        )}
      </div>
      <div className="space-y-1 p-3">
        <p className="truncate text-sm font-medium">{item.filename}</p>
        <p className="text-xs text-muted-foreground">
          {categoryLabel(t, item.category)}
          {" · "}
          {lateralityLabel(t, item.laterality)}
        </p>
        <p className="text-xs text-muted-foreground">
          {when
            ? formatDateTimeInTimeZone(when, timeZone, locale)
            : t("gallery.noDate")}
        </p>
        {item.bodySite?.display ? (
          <p className="truncate text-xs">{item.bodySite.display}</p>
        ) : null}
        <p className="text-xs text-muted-foreground">
          {t("gallery.teaching")}:{" "}
          {consentLabel(t, item.isConsentedForTeaching)}
          {" · "}
          {processingLabel(t, item.processingStatus)}
        </p>
      </div>
    </button>
  );
}
