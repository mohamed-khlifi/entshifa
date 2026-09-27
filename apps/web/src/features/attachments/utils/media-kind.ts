import type { MediaVariantRead } from "@/lib/api/generated";

export type MediaKind = "image" | "video" | "audio" | "document";

const IMAGE_CATEGORIES = new Set([
  "endoscopy_image",
  "clinical_photo",
  "audiogram_scan",
  "signature",
  "logo",
]);

export function mediaKind(category: string, contentType: string): MediaKind {
  if (category === "endoscopy_video" || contentType.startsWith("video/")) {
    return "video";
  }
  if (category === "voice_recording" || contentType.startsWith("audio/")) {
    return "audio";
  }
  if (IMAGE_CATEGORIES.has(category) || contentType.startsWith("image/")) {
    return "image";
  }
  return "document";
}

export function listVariant(variants: MediaVariantRead[]): string | undefined {
  return (
    variants.find((item) => item.variant === "thumb")?.variant ??
    variants.find((item) => item.variant === "preview")?.variant
  );
}

export function viewerVariant(
  variants: MediaVariantRead[],
): string | undefined {
  return (
    variants.find((item) => item.variant === "preview")?.variant ??
    variants.find((item) => item.variant === "web")?.variant ??
    variants.find((item) => item.variant === "thumb")?.variant
  );
}

export function acceptForCategory(category: string): string {
  switch (category) {
    case "endoscopy_video":
      return "video/mp4,video/webm";
    case "endoscopy_image":
    case "clinical_photo":
      return "image/jpeg,image/png,image/webp";
    case "audiogram_scan":
    case "imaging_report":
    case "pathology":
    case "external_letter":
    case "document_pdf":
      return "application/pdf,image/jpeg,image/png,image/webp";
    default:
      return "application/pdf,image/jpeg,image/png,image/webp,video/mp4";
  }
}

const BYTE_UNITS = ["B", "KB", "MB", "GB"] as const;

export function formatByteSize(bytes: number, locale: string): string {
  const safe = Number.isFinite(bytes) && bytes > 0 ? bytes : 0;
  let value = safe;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < BYTE_UNITS.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  const formatted =
    unitIndex === 0
      ? new Intl.NumberFormat(locale, { maximumFractionDigits: 0 }).format(
          value,
        )
      : new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(
          value,
        );
  return `${formatted} ${BYTE_UNITS[unitIndex]}`;
}

export function uploadPercent(loaded: number, total: number): number {
  if (total <= 0) {
    return 0;
  }
  return Math.min(100, Math.round((loaded / total) * 100));
}
