"use client";

import { useLocale, useTranslations } from "next-intl";
import { useMemo, useRef, useState } from "react";

import { useCurrentClinicQuery } from "@/features/clinics";
import { BodySiteField } from "../components/BodySiteField";
import { AttachmentUploadProgress } from "../components/AttachmentUploadProgress";
import type { UploadPhase } from "../components/AttachmentUploadProgress";
import {
  EXTERNAL_DOCUMENT_CATEGORIES,
  LATERALITY_VALUES,
  MAX_UPLOAD_BYTES,
  PATIENT_ATTACHMENT_CATEGORIES,
} from "../constants";
import { useUploadAttachmentMutation } from "../hooks/use-attachment-queries";
import { categoryLabel, lateralityLabel, presetLabel } from "../labels";
import {
  createAttachmentUploadSchema,
  type AttachmentUploadFormValues,
} from "../schemas/attachment-upload.schema";
import { dateTimeLocalToUtcIso } from "../utils/captured-at";
import { acceptForCategory, formatByteSize } from "../utils/media-kind";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useClinicalForm } from "@/lib/forms/createForm";
import { testId, testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

type AttachmentUploadPanelProps = {
  patientPublicId: string;
  onUploaded: () => void;
};

type FileError = "fileRequired" | "fileTooLarge" | "unauthenticated";

const PRESETS: {
  category: (typeof PATIENT_ATTACHMENT_CATEGORIES)[number];
  id: string;
}[] = [
  { category: "endoscopy_image", id: "endoscopy-image" },
  { category: "endoscopy_video", id: "endoscopy-video" },
  { category: "clinical_photo", id: "clinical-photo" },
  { category: "audiogram_scan", id: "audiogram-scan" },
  { category: "imaging_report", id: "imaging-report" },
  { category: "pathology", id: "pathology" },
  { category: "external_letter", id: "external-letter" },
  { category: "document_pdf", id: "document-pdf" },
];

export function AttachmentUploadPanel({
  patientPublicId,
  onUploaded,
}: AttachmentUploadPanelProps) {
  const t = useTranslations("attachments");
  const locale = useLocale();
  const { session } = useSession();
  const clinic = useCurrentClinicQuery();
  const timeZone = clinic.data?.timezone ?? "UTC";
  const upload = useUploadAttachmentMutation();
  const schema = useMemo(() => createAttachmentUploadSchema(t), [t]);
  const lastValues = useRef<AttachmentUploadFormValues | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<UploadPhase>("idle");
  const [loaded, setLoaded] = useState(0);
  const [total, setTotal] = useState(0);
  const [fileError, setFileError] = useState<FileError | null>(null);

  const { form, handleSubmit } = useClinicalForm({
    schema,
    defaultValues: {
      category: "clinical_photo",
      laterality: "",
      bodySiteConceptId: "",
      bodySiteDisplay: "",
      capturedAt: "",
      caption: "",
      isConsentedForTeaching: false,
    },
    onSubmit: async (values) => {
      lastValues.current = values;
      await runUpload(values);
    },
  });

  const category = form.watch("category");
  const busy = upload.isPending;

  async function runUpload(values: AttachmentUploadFormValues) {
    if (!session?.clinicPublicId) {
      setFileError("unauthenticated");
      return;
    }
    if (!file) {
      setFileError("fileRequired");
      return;
    }
    if (file.size > MAX_UPLOAD_BYTES || file.size < 1) {
      setFileError("fileTooLarge");
      return;
    }
    setFileError(null);
    setPhase("requesting");
    setLoaded(0);
    setTotal(file.size);
    const capturedAt = values.capturedAt
      ? dateTimeLocalToUtcIso(values.capturedAt, timeZone)
      : null;
    try {
      await upload.mutateAsync({
        file,
        body: {
          category: values.category,
          filename: file.name,
          contentType: file.type || "application/octet-stream",
          sizeBytes: file.size,
          patientPublicId,
          caption: values.caption.trim() || null,
          laterality: values.laterality === "" ? null : values.laterality,
          bodySiteConceptId: values.bodySiteConceptId || null,
          capturedAt,
          isConsentedForTeaching: values.isConsentedForTeaching,
        },
        onProgress: (nextLoaded, nextTotal) => {
          setLoaded(nextLoaded);
          setTotal(nextTotal);
          setPhase(
            nextTotal > 0 && nextLoaded >= nextTotal
              ? "confirming"
              : "uploading",
          );
        },
      });
      setPhase("idle");
      setFile(null);
      form.reset();
      onUploaded();
    } catch {
      setPhase("failed");
    }
  }

  const fileErrorText =
    fileError === "fileRequired"
      ? t("upload.errors.fileRequired")
      : fileError === "fileTooLarge"
        ? t("upload.errors.fileTooLarge")
        : fileError === "unauthenticated"
          ? t("upload.errors.unauthenticated")
          : null;

  return (
    <Card {...testIdProps(testIds.attachments.uploadPanel)}>
      <CardHeader>
        <CardTitle>{t("upload.title")}</CardTitle>
        <p className="text-sm text-muted-foreground">
          {t("upload.description")}
        </p>
        <p className="text-sm text-muted-foreground">
          {t("upload.maxHint", {
            size: formatByteSize(MAX_UPLOAD_BYTES, locale),
          })}
        </p>
      </CardHeader>
      <CardContent>
        <form
          className="space-y-4"
          onSubmit={(event) => void handleSubmit(event)}
        >
          <div className="space-y-3">
            <div className="space-y-2">
              <p className="text-sm font-medium">{t("upload.captureTitle")}</p>
              <div className="flex flex-wrap gap-2">
                {PRESETS.filter(
                  (preset) =>
                    !(
                      EXTERNAL_DOCUMENT_CATEGORIES as readonly string[]
                    ).includes(preset.category),
                ).map((preset) => (
                  <Button
                    key={preset.category}
                    type="button"
                    size="sm"
                    variant={
                      category === preset.category ? "default" : "secondary"
                    }
                    onClick={() => form.setValue("category", preset.category)}
                    {...testIdProps(testId("attachments", "preset", preset.id))}
                  >
                    {presetLabel(t, preset.category)}
                  </Button>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">{t("upload.externalTitle")}</p>
              <div className="flex flex-wrap gap-2">
                {PRESETS.filter((preset) =>
                  (EXTERNAL_DOCUMENT_CATEGORIES as readonly string[]).includes(
                    preset.category,
                  ),
                ).map((preset) => (
                  <Button
                    key={preset.category}
                    type="button"
                    size="sm"
                    variant={
                      category === preset.category ? "default" : "secondary"
                    }
                    onClick={() => form.setValue("category", preset.category)}
                    {...testIdProps(testId("attachments", "preset", preset.id))}
                  >
                    {presetLabel(t, preset.category)}
                  </Button>
                ))}
              </div>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor={testIds.attachments.uploadCategory}>
                {t("upload.category")}
              </Label>
              <Select
                id={testIds.attachments.uploadCategory}
                disabled={busy}
                {...form.register("category")}
                {...testIdProps(testIds.attachments.uploadCategory)}
              >
                {PATIENT_ATTACHMENT_CATEGORIES.map((value) => (
                  <option key={value} value={value}>
                    {categoryLabel(t, value)}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor={testIds.attachments.uploadLaterality}>
                {t("upload.laterality")}
              </Label>
              <Select
                id={testIds.attachments.uploadLaterality}
                disabled={busy}
                {...form.register("laterality")}
                {...testIdProps(testIds.attachments.uploadLaterality)}
              >
                <option value="">{t("laterality.unspecified")}</option>
                {LATERALITY_VALUES.map((value) => (
                  <option key={value} value={value}>
                    {lateralityLabel(t, value)}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor={testIds.attachments.uploadCapturedAt}>
                {t("upload.capturedAt")}
              </Label>
              <Input
                id={testIds.attachments.uploadCapturedAt}
                type="datetime-local"
                disabled={busy}
                {...form.register("capturedAt")}
                {...testIdProps(testIds.attachments.uploadCapturedAt)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor={testIds.attachments.uploadCaption}>
                {t("upload.caption")}
              </Label>
              <Input
                id={testIds.attachments.uploadCaption}
                disabled={busy}
                {...form.register("caption")}
                {...testIdProps(testIds.attachments.uploadCaption)}
              />
            </div>
          </div>
          <BodySiteField
            selectedId={form.watch("bodySiteConceptId")}
            selectedDisplay={form.watch("bodySiteDisplay")}
            onSelect={(concept) => {
              form.setValue("bodySiteConceptId", concept.publicId);
              form.setValue("bodySiteDisplay", concept.display);
            }}
            onClear={() => {
              form.setValue("bodySiteConceptId", "");
              form.setValue("bodySiteDisplay", "");
            }}
          />
          <div className="space-y-1.5">
            <Label htmlFor={testIds.attachments.uploadFile}>
              {t("upload.file")}
            </Label>
            <Input
              id={testIds.attachments.uploadFile}
              type="file"
              accept={acceptForCategory(category)}
              disabled={busy}
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                setFileError(null);
              }}
              {...testIdProps(testIds.attachments.uploadFile)}
            />
          </div>
          <label className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              className="mt-1 size-4 rounded border-input"
              disabled={busy}
              {...form.register("isConsentedForTeaching")}
              {...testIdProps(testIds.attachments.uploadConsent)}
            />
            <span>
              <span className="font-medium">{t("upload.consent")}</span>
              <span className="mt-0.5 block text-muted-foreground">
                {t("upload.consentHint")}
              </span>
            </span>
          </label>
          {fileErrorText ? (
            <p className="text-sm text-destructive" role="alert">
              {fileErrorText}
            </p>
          ) : null}
          <AttachmentUploadProgress
            phase={phase}
            loaded={loaded}
            total={total}
            loadedLabel={formatByteSize(loaded, locale)}
            totalLabel={formatByteSize(total, locale)}
            onRetry={() => {
              if (lastValues.current) {
                void runUpload(lastValues.current);
              }
            }}
          />
          <Button
            type="submit"
            disabled={busy}
            {...testIdProps(testIds.attachments.uploadSubmit)}
          >
            {busy ? t("upload.submitting") : t("upload.submit")}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
