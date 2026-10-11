"use client";

import { useQuery } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { EndoscopyAnnotator } from "./EndoscopyAnnotator";
import {
  fetchAttachmentDownloadUrl,
  fetchAttachments,
  useUploadAttachmentMutation,
} from "@/features/attachments";
import type { AttachmentRead } from "@/lib/api/generated";
import { queryKeys } from "@/lib/api/query-keys";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

type EndoscopyMediaPanelProps = {
  patientId: string;
  bodySiteCode: string | null;
  bodySitePublicId: string | null;
  laterality: "right" | "left" | "midline";
  readOnly: boolean;
};

function byNewest(left: AttachmentRead, right: AttachmentRead): number {
  const leftAt = Date.parse(left.capturedAt ?? left.createdAt ?? "");
  const rightAt = Date.parse(right.capturedAt ?? right.createdAt ?? "");
  return (
    (Number.isNaN(rightAt) ? 0 : rightAt) - (Number.isNaN(leftAt) ? 0 : leftAt)
  );
}

export function EndoscopyMediaPanel({
  patientId,
  bodySiteCode,
  bodySitePublicId,
  laterality,
  readOnly,
}: EndoscopyMediaPanelProps) {
  const t = useTranslations("endoscopy");
  const locale = useLocale();
  const { session } = useSession();
  const upload = useUploadAttachmentMutation();
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraOn, setCameraOn] = useState(false);
  const [annotatingId, setAnnotatingId] = useState<string | null>(null);
  const clinicPublicId = session?.clinicPublicId ?? "";
  const attachments = useQuery({
    queryKey: queryKeys.attachments.list({
      patientPublicId: patientId,
      category: "endoscopy_image",
      limit: 100,
    }),
    queryFn: () =>
      fetchAttachments(
        { locale, clinicPublicId },
        {
          patientPublicId: patientId,
          category: "endoscopy_image",
          limit: 100,
        },
      ),
    enabled: clinicPublicId.length > 0 && patientId.length > 0,
    staleTime: 15_000,
  });

  const matched = useMemo(() => {
    const items = attachments.data?.items ?? [];
    return items
      .filter(
        (item) =>
          item.bodySite?.code === bodySiteCode &&
          item.laterality === laterality,
      )
      .sort(byNewest);
  }, [attachments.data?.items, bodySiteCode, laterality]);
  const current = matched[0] ?? null;
  const previous = matched[1] ?? null;
  const currentUrl = useImageUrl(current?.publicId ?? null);
  const previousUrl = useImageUrl(previous?.publicId ?? null);

  async function send(file: File) {
    if (!bodySitePublicId) {
      return;
    }
    await upload.mutateAsync({
      file,
      onProgress: () => undefined,
      body: {
        category: "endoscopy_image",
        filename: file.name,
        contentType: file.type || "image/png",
        sizeBytes: file.size,
        patientPublicId: patientId,
        laterality,
        bodySiteConceptId: bodySitePublicId,
        capturedAt: new Date().toISOString(),
        isConsentedForTeaching: false,
      },
    });
  }

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraOn(true);
    } catch {
      toast.error(t("images.cameraError"));
    }
  }

  function stopCamera() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setCameraOn(false);
  }

  function snap() {
    const video = videoRef.current;
    if (!video) {
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }
    context.drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob) {
        return;
      }
      const file = new File([blob], "endoscopy-capture.png", {
        type: "image/png",
      });
      void send(file);
      stopCamera();
    }, "image/png");
  }

  if (!bodySiteCode) {
    return (
      <p
        className="text-sm text-muted-foreground"
        {...testIdProps(testIds.endoscopy.images)}
      >
        {t("images.pickStructure")}
      </p>
    );
  }

  return (
    <section className="space-y-3" {...testIdProps(testIds.endoscopy.images)}>
      <h3 className="text-sm font-semibold">{t("images.title")}</h3>
      <div className="flex flex-wrap gap-2">
        <label className="inline-flex cursor-pointer items-center rounded-lg border border-border px-3 py-2 text-sm">
          {t("images.upload")}
          <input
            type="file"
            accept="image/*"
            className="sr-only"
            disabled={readOnly || !bodySitePublicId || upload.isPending}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) {
                void send(file);
              }
              event.target.value = "";
            }}
            {...testIdProps(testIds.endoscopy.imagesUpload)}
          />
        </label>
        {cameraOn ? (
          <>
            <button
              type="button"
              className="rounded-lg border border-border px-3 py-2 text-sm"
              onClick={snap}
              {...testIdProps(testIds.endoscopy.imagesSnap)}
            >
              {t("images.snap")}
            </button>
            <button
              type="button"
              className="rounded-lg border border-border px-3 py-2 text-sm"
              onClick={stopCamera}
              {...testIdProps(testIds.endoscopy.imagesStop)}
            >
              {t("images.stop")}
            </button>
          </>
        ) : (
          <button
            type="button"
            className="rounded-lg border border-border px-3 py-2 text-sm"
            disabled={readOnly}
            onClick={() => void startCamera()}
            {...testIdProps(testIds.endoscopy.imagesCapture)}
          >
            {t("images.capture")}
          </button>
        )}
      </div>
      {cameraOn ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="max-w-md rounded-xl"
        />
      ) : null}
      {matched.length === 0 ? (
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.endoscopy.imagesEmpty)}
        >
          {t("images.empty")}
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          <ImagePair
            title={t("images.current")}
            url={currentUrl.data?.download.url ?? null}
            onAnnotate={
              current && currentUrl.data?.download.url
                ? () => setAnnotatingId(current.publicId)
                : null
            }
          />
          <ImagePair
            title={t("images.previous")}
            url={previousUrl.data?.download.url ?? null}
          />
        </div>
      )}
      {annotatingId && currentUrl.data?.download.url ? (
        <EndoscopyAnnotator
          imageUrl={currentUrl.data.download.url}
          storageKey={`endoscopy-annotation:${annotatingId}`}
          readOnly={readOnly}
          onClose={() => setAnnotatingId(null)}
        />
      ) : null}
    </section>
  );
}

function ImagePair({
  title,
  url,
  onAnnotate,
}: {
  title: string;
  url: string | null;
  onAnnotate?: (() => void) | null;
}) {
  const t = useTranslations("endoscopy");
  return (
    <figure className="space-y-2">
      <figcaption className="text-xs font-medium text-muted-foreground">
        {title}
      </figcaption>
      {url ? (
        // Signed download URLs must render the original bytes, not a rewritten optimizer URL.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={url}
          alt=""
          className="w-full rounded-xl border border-border"
        />
      ) : (
        <p className="text-sm text-muted-foreground">{t("images.empty")}</p>
      )}
      {onAnnotate ? (
        <button
          type="button"
          className="text-sm font-medium text-primary"
          onClick={onAnnotate}
          {...testIdProps(testIds.endoscopy.imagesAnnotate)}
        >
          {t("images.annotate")}
        </button>
      ) : null}
    </figure>
  );
}

function useImageUrl(publicId: string | null) {
  const locale = useLocale();
  const { session } = useSession();
  const clinicPublicId = session?.clinicPublicId ?? "";
  return useQuery({
    queryKey: queryKeys.attachments.download(publicId ?? "", undefined),
    queryFn: () =>
      fetchAttachmentDownloadUrl(publicId ?? "", locale, clinicPublicId),
    enabled: Boolean(publicId && clinicPublicId),
    staleTime: 30_000,
  });
}
