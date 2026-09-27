"use client";

import { useLocale, useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { useCurrentClinicQuery } from "@/features/clinics";
import { AttachmentCard } from "../components/AttachmentCard";
import { AttachmentDetailViewer } from "../components/AttachmentDetailViewer";
import { AttachmentUploadPanel } from "../components/AttachmentUploadPanel";
import {
  GALLERY_PAGE_SIZE,
  LATERALITY_VALUES,
  PATIENT_ATTACHMENT_CATEGORIES,
} from "../constants";
import { useAttachmentsQuery } from "../hooks/use-attachment-queries";
import { categoryLabel, lateralityLabel } from "../labels";
import {
  nextClinicDayUtcIso,
  startOfClinicDayUtcIso,
} from "../utils/captured-at";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import type { AttachmentRead } from "@/lib/api/generated";
import { Permission } from "@/lib/permissions";
import { usePathname, useRouter } from "@/lib/i18n/navigation";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { usePermission } from "@/providers/permission-provider";

type AttachmentGalleryProps = {
  patientPublicId: string;
};

export function AttachmentGallery({ patientPublicId }: AttachmentGalleryProps) {
  const t = useTranslations("attachments");
  const locale = useLocale();
  const canRead = usePermission(Permission.ATTACHMENT_READ);
  const canWrite = usePermission(Permission.ATTACHMENT_WRITE);
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const clinic = useCurrentClinicQuery();
  const timeZone = clinic.data?.timezone ?? "UTC";
  const [uploadOpen, setUploadOpen] = useState(false);
  const [selected, setSelected] = useState<AttachmentRead | null>(null);

  const category = searchParams.get("category") ?? "";
  const laterality = searchParams.get("laterality") ?? "";
  const from = searchParams.get("from") ?? "";
  const to = searchParams.get("to") ?? "";
  const offset = Number(searchParams.get("offset") ?? "0") || 0;

  const filters = useMemo(
    () => ({
      patientPublicId,
      category: category || undefined,
      laterality: laterality || undefined,
      capturedFrom: from
        ? (startOfClinicDayUtcIso(from, timeZone) ?? undefined)
        : undefined,
      capturedTo: to
        ? (nextClinicDayUtcIso(to, timeZone) ?? undefined)
        : undefined,
      limit: GALLERY_PAGE_SIZE,
      offset,
    }),
    [patientPublicId, category, laterality, from, to, offset, timeZone],
  );

  const attachments = useAttachmentsQuery(filters);

  if (!canRead) {
    return (
      <p
        className="text-sm text-muted-foreground"
        {...testIdProps(testIds.attachments.forbidden)}
      >
        {t("forbidden")}
      </p>
    );
  }

  const replaceParams = (patch: Record<string, string>) => {
    const next = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(patch)) {
      if (value) {
        next.set(key, value);
      } else {
        next.delete(key);
      }
    }
    if (!("offset" in patch)) {
      next.delete("offset");
    }
    const text = next.toString();
    router.replace(text ? `${pathname}?${text}` : pathname);
  };

  const items = attachments.data?.items ?? [];
  const total = attachments.data?.page.total ?? 0;

  return (
    <section
      className="space-y-6"
      {...testIdProps(testIds.attachments.gallery)}
    >
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold tracking-tight">
            {t("gallery.title")}
          </h2>
          <p className="max-w-2xl text-sm text-muted-foreground">
            {t("gallery.description")}
          </p>
        </div>
        {canWrite ? (
          <Button
            type="button"
            onClick={() => setUploadOpen((open) => !open)}
            {...testIdProps(testIds.attachments.uploadOpen)}
          >
            {t("upload.open")}
          </Button>
        ) : null}
      </div>
      {uploadOpen && canWrite ? (
        <AttachmentUploadPanel
          patientPublicId={patientPublicId}
          onUploaded={() => setUploadOpen(false)}
        />
      ) : null}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="space-y-1.5">
          <Label htmlFor={testIds.attachments.filterCategory}>
            {t("filter.category")}
          </Label>
          <Select
            id={testIds.attachments.filterCategory}
            value={category}
            onChange={(event) =>
              replaceParams({ category: event.target.value })
            }
            {...testIdProps(testIds.attachments.filterCategory)}
          >
            <option value="">{t("filter.any")}</option>
            {PATIENT_ATTACHMENT_CATEGORIES.map((value) => (
              <option key={value} value={value}>
                {categoryLabel(t, value)}
              </option>
            ))}
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor={testIds.attachments.filterLaterality}>
            {t("filter.laterality")}
          </Label>
          <Select
            id={testIds.attachments.filterLaterality}
            value={laterality}
            onChange={(event) =>
              replaceParams({ laterality: event.target.value })
            }
            {...testIdProps(testIds.attachments.filterLaterality)}
          >
            <option value="">{t("filter.any")}</option>
            {LATERALITY_VALUES.map((value) => (
              <option key={value} value={value}>
                {lateralityLabel(t, value)}
              </option>
            ))}
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor={testIds.attachments.filterFrom}>
            {t("filter.from")}
          </Label>
          <input
            id={testIds.attachments.filterFrom}
            type="date"
            lang={locale}
            value={from}
            onChange={(event) => replaceParams({ from: event.target.value })}
            className="flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
            {...testIdProps(testIds.attachments.filterFrom)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor={testIds.attachments.filterTo}>{t("filter.to")}</Label>
          <input
            id={testIds.attachments.filterTo}
            type="date"
            lang={locale}
            value={to}
            onChange={(event) => replaceParams({ to: event.target.value })}
            className="flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
            {...testIdProps(testIds.attachments.filterTo)}
          />
        </div>
      </div>
      {attachments.isLoading ? (
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.attachments.galleryLoading)}
        >
          {t("gallery.loading")}
        </p>
      ) : null}
      {attachments.isError ? (
        <p
          className="text-sm text-destructive"
          role="alert"
          {...testIdProps(testIds.attachments.galleryError)}
        >
          {t("gallery.error")}
        </p>
      ) : null}
      {!attachments.isLoading && !attachments.isError && items.length === 0 ? (
        <div
          className="rounded-xl border border-dashed border-border px-4 py-10 text-center"
          {...testIdProps(testIds.attachments.galleryEmpty)}
        >
          <p className="font-medium">{t("gallery.emptyTitle")}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("gallery.emptyDescription")}
          </p>
        </div>
      ) : null}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <AttachmentCard
            key={item.publicId}
            item={item}
            onOpen={setSelected}
          />
        ))}
      </div>
      {total > GALLERY_PAGE_SIZE ? (
        <div className="flex items-center justify-between gap-3">
          <Button
            type="button"
            variant="secondary"
            disabled={offset <= 0}
            onClick={() =>
              replaceParams({
                offset: String(Math.max(0, offset - GALLERY_PAGE_SIZE)),
                category,
                laterality,
                from,
                to,
              })
            }
            {...testIdProps(testIds.attachments.pagePrev)}
          >
            {t("gallery.previous")}
          </Button>
          <p className="text-sm text-muted-foreground">
            {t("gallery.page", {
              from: offset + 1,
              to: Math.min(offset + items.length, total),
              total,
            })}
          </p>
          <Button
            type="button"
            variant="secondary"
            disabled={offset + GALLERY_PAGE_SIZE >= total}
            onClick={() =>
              replaceParams({
                offset: String(offset + GALLERY_PAGE_SIZE),
                category,
                laterality,
                from,
                to,
              })
            }
            {...testIdProps(testIds.attachments.pageNext)}
          >
            {t("gallery.next")}
          </Button>
        </div>
      ) : null}
      {selected ? (
        <AttachmentDetailViewer
          item={selected}
          onClose={() => setSelected(null)}
        />
      ) : null}
    </section>
  );
}
