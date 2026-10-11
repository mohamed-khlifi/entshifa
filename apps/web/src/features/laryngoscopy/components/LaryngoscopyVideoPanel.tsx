"use client";

import { useQuery } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useRef, useState } from "react";
import { toast } from "sonner";

import {
  fetchAttachmentDownloadUrl,
  fetchAttachments,
  useUploadAttachmentMutation,
} from "@/features/attachments";
import { VIDEO_MAX_MS } from "../lib/draft";
import { queryKeys } from "@/lib/api/query-keys";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

type LaryngoscopyVideoPanelProps = {
  patientId: string;
  procedureId: string | null;
  previousProcedureId: string | null;
  bodySitePublicId: string | null;
  laterality: "right" | "left" | "midline";
  readOnly: boolean;
};

export function LaryngoscopyVideoPanel({
  patientId,
  procedureId,
  previousProcedureId,
  bodySitePublicId,
  laterality,
  readOnly,
}: LaryngoscopyVideoPanelProps) {
  const t = useTranslations("laryngoscopy");
  const locale = useLocale();
  const { session } = useSession();
  const upload = useUploadAttachmentMutation();
  const liveRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const [cameraOn, setCameraOn] = useState(false);
  const clinicPublicId = session?.clinicPublicId ?? "";
  const currentClips = useQuery({
    queryKey: queryKeys.attachments.list({
      patientPublicId: patientId,
      category: "endoscopy_video",
      procedurePublicId: procedureId ?? undefined,
      limit: 20,
    }),
    queryFn: () =>
      fetchAttachments(
        { locale, clinicPublicId },
        {
          patientPublicId: patientId,
          category: "endoscopy_video",
          procedurePublicId: procedureId ?? undefined,
          limit: 20,
        },
      ),
    enabled: clinicPublicId.length > 0 && Boolean(procedureId),
    staleTime: 15_000,
  });
  const previousClips = useQuery({
    queryKey: queryKeys.attachments.list({
      patientPublicId: patientId,
      category: "endoscopy_video",
      procedurePublicId: previousProcedureId ?? undefined,
      limit: 20,
    }),
    queryFn: () =>
      fetchAttachments(
        { locale, clinicPublicId },
        {
          patientPublicId: patientId,
          category: "endoscopy_video",
          procedurePublicId: previousProcedureId ?? undefined,
          limit: 20,
        },
      ),
    enabled: clinicPublicId.length > 0 && Boolean(previousProcedureId),
    staleTime: 15_000,
  });
  const current = currentClips.data?.items[0] ?? null;
  const previous = previousClips.data?.items[0] ?? null;
  const currentUrl = useClipUrl(current?.publicId ?? null);
  const previousUrl = useClipUrl(previous?.publicId ?? null);

  async function send(file: File) {
    if (!procedureId) {
      toast.error(t("video.needsStudy"));
      return;
    }
    await upload.mutateAsync({
      file,
      onProgress: () => undefined,
      body: {
        category: "endoscopy_video",
        filename: file.name,
        contentType: file.type || "video/webm",
        sizeBytes: file.size,
        patientPublicId: patientId,
        procedurePublicId: procedureId,
        laterality,
        bodySiteConceptId: bodySitePublicId,
        capturedAt: new Date().toISOString(),
        isConsentedForTeaching: false,
      },
    });
  }

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      });
      streamRef.current = stream;
      if (liveRef.current) {
        liveRef.current.srcObject = stream;
      }
      setCameraOn(true);
    } catch {
      toast.error(t("video.cameraError"));
    }
  }

  function stopCamera() {
    recorderRef.current?.stop();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setCameraOn(false);
  }

  function startRecording() {
    const stream = streamRef.current;
    if (!stream) {
      return;
    }
    chunksRef.current = [];
    const recorder = new MediaRecorder(stream);
    recorderRef.current = recorder;
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, {
        type: recorder.mimeType || "video/webm",
      });
      if (blob.size === 0) {
        return;
      }
      const file = new File([blob], `laryngoscopy-${Date.now()}.webm`, {
        type: blob.type,
      });
      void send(file);
    };
    recorder.start();
    timerRef.current = window.setTimeout(() => {
      recorder.stop();
      toast.error(t("video.tooLong"));
    }, VIDEO_MAX_MS);
  }

  return (
    <section className="space-y-3" {...testIdProps(testIds.laryngoscopy.video)}>
      <h3 className="text-sm font-semibold">{t("video.title")}</h3>
      {!procedureId ? (
        <p className="text-sm text-muted-foreground">{t("video.needsStudy")}</p>
      ) : null}
      {procedureId && !bodySitePublicId ? (
        <p className="text-sm text-muted-foreground">
          {t("video.pickStructure")}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <label>
          <span className="sr-only">{t("video.upload")}</span>
          <input
            type="file"
            accept="video/mp4,video/webm"
            disabled={readOnly || !procedureId}
            className="text-sm"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) {
                void send(file);
              }
              event.target.value = "";
            }}
            {...testIdProps(testIds.laryngoscopy.videoUpload)}
          />
        </label>
        <button
          type="button"
          className="rounded-lg border border-border px-3 py-1.5 text-sm"
          disabled={readOnly}
          onClick={() => (cameraOn ? stopCamera() : void startCamera())}
          {...testIdProps(
            cameraOn
              ? testIds.laryngoscopy.videoStop
              : testIds.laryngoscopy.videoCapture,
          )}
        >
          {cameraOn ? t("video.stop") : t("video.capture")}
        </button>
        {cameraOn ? (
          <button
            type="button"
            className="rounded-lg border border-border px-3 py-1.5 text-sm"
            disabled={readOnly || !procedureId}
            onClick={startRecording}
            {...testIdProps(testIds.laryngoscopy.videoRecord)}
          >
            {t("video.record")}
          </button>
        ) : null}
      </div>
      {cameraOn ? (
        <video
          ref={liveRef}
          autoPlay
          muted
          playsInline
          className="w-full rounded-xl"
        />
      ) : null}
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-1 text-xs text-muted-foreground">
            {t("video.current")}
          </p>
          {currentUrl ? (
            <video
              controls
              playsInline
              src={currentUrl}
              className="w-full rounded-xl bg-foreground/10"
              {...testIdProps(testIds.laryngoscopy.videoCurrent)}
            />
          ) : (
            <p
              className="text-sm text-muted-foreground"
              {...testIdProps(testIds.laryngoscopy.videoEmpty)}
            >
              {t("video.empty")}
            </p>
          )}
        </div>
        <div>
          <p className="mb-1 text-xs text-muted-foreground">
            {t("video.previous")}
          </p>
          {previousUrl ? (
            <video
              controls
              playsInline
              src={previousUrl}
              className="w-full rounded-xl bg-foreground/10"
              {...testIdProps(testIds.laryngoscopy.videoPrevious)}
            />
          ) : null}
        </div>
      </div>
    </section>
  );
}

function useClipUrl(publicId: string | null): string | null {
  const locale = useLocale();
  const { session } = useSession();
  const clinicPublicId = session?.clinicPublicId ?? "";
  const query = useQuery({
    queryKey: queryKeys.attachments.download(publicId ?? "", undefined),
    queryFn: () =>
      fetchAttachmentDownloadUrl(publicId ?? "", locale, clinicPublicId),
    enabled: Boolean(publicId) && clinicPublicId.length > 0,
    staleTime: 30_000,
  });
  return query.data?.download.url ?? null;
}
