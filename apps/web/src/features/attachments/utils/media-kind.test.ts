import { describe, expect, it } from "vitest";

import { formatByteSize, mediaKind, uploadPercent } from "./media-kind";

describe("mediaKind", () => {
  it("keeps endoscopy video out of the image thumbnail path", () => {
    expect(mediaKind("endoscopy_video", "video/mp4")).toBe("video");
    expect(mediaKind("endoscopy_image", "image/jpeg")).toBe("image");
    expect(mediaKind("external_letter", "application/pdf")).toBe("document");
    expect(mediaKind("voice_recording", "audio/mpeg")).toBe("audio");
  });
});

describe("uploadPercent", () => {
  it("clamps progress to the file size", () => {
    expect(uploadPercent(50, 200)).toBe(25);
    expect(uploadPercent(0, 0)).toBe(0);
    expect(uploadPercent(500, 100)).toBe(100);
  });
});

describe("formatByteSize", () => {
  it("keeps unit symbols untranslated", () => {
    expect(formatByteSize(200 * 1024 * 1024, "en")).toContain("MB");
    expect(formatByteSize(0, "en")).toBe("0 B");
  });
});
