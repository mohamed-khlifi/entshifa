import { describe, expect, it, vi } from "vitest";

import {
  StorageUploadError,
  putFileWithRetry,
  putPresignedFile,
} from "./direct-upload";

describe("putFileWithRetry", () => {
  it("retries a failed storage put and then succeeds", async () => {
    const put = vi
      .fn()
      .mockRejectedValueOnce(new StorageUploadError())
      .mockRejectedValueOnce(new StorageUploadError())
      .mockResolvedValueOnce(undefined);

    await putFileWithRetry(put, 3);

    expect(put).toHaveBeenCalledTimes(3);
  });

  it("throws after the last failed attempt", async () => {
    const put = vi.fn().mockRejectedValue(new StorageUploadError());
    await expect(putFileWithRetry(put, 2)).rejects.toBeInstanceOf(
      StorageUploadError,
    );
    expect(put).toHaveBeenCalledTimes(2);
  });
});

describe("putPresignedFile", () => {
  it("sends the file to the pre-signed URL and reports progress", async () => {
    const headers: Record<string, string> = {};
    let sent: unknown;
    const xhr = {
      status: 200,
      upload: {} as { onprogress: ((event: ProgressEvent) => void) | null },
      open: vi.fn(),
      setRequestHeader: (key: string, value: string) => {
        headers[key] = value;
      },
      send: (body: unknown) => {
        sent = body;
        xhr.upload.onprogress?.({
          lengthComputable: true,
          loaded: 50,
          total: 100,
        } as ProgressEvent);
        xhr.onload?.();
      },
      onload: null as (() => void) | null,
      onerror: null as (() => void) | null,
      onabort: null as (() => void) | null,
    };
    const file = new Blob(["clinical"], { type: "image/jpeg" });
    const onProgress = vi.fn();

    await putPresignedFile(
      {
        url: "https://storage.example/upload",
        method: "PUT",
        headers: { "Content-Type": "image/jpeg" },
      },
      file,
      onProgress,
      () => xhr as unknown as XMLHttpRequest,
    );

    expect(xhr.open).toHaveBeenCalledWith(
      "PUT",
      "https://storage.example/upload",
    );
    expect(headers["Content-Type"]).toBe("image/jpeg");
    expect(sent).toBe(file);
    expect(onProgress).toHaveBeenCalledWith(50, 100);
  });
});
