/**
 * Bytes go to object storage with the pre-signed URL.
 * They never pass through the API process.
 */

export const STORAGE_UPLOAD_ATTEMPTS = 3;

export class StorageUploadError extends Error {
  readonly code = "storage_upload_failed";
}

export type PresignedTarget = {
  url: string;
  method: string;
  headers: Record<string, string>;
};

export async function putFileWithRetry(
  put: () => Promise<void>,
  attempts = STORAGE_UPLOAD_ATTEMPTS,
): Promise<void> {
  let last: unknown;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      await put();
      return;
    } catch (error) {
      last = error;
    }
  }
  if (last instanceof StorageUploadError) {
    throw last;
  }
  throw new StorageUploadError();
}

export function putPresignedFile(
  target: PresignedTarget,
  file: Blob,
  onProgress: (loaded: number, total: number) => void,
  xhrFactory: () => XMLHttpRequest = () => new XMLHttpRequest(),
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = xhrFactory();
    xhr.open(target.method, target.url);
    for (const [key, value] of Object.entries(target.headers)) {
      xhr.setRequestHeader(key, value);
    }
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress(event.loaded, event.total);
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
        return;
      }
      reject(new StorageUploadError());
    };
    xhr.onerror = () => {
      reject(new StorageUploadError());
    };
    xhr.onabort = () => {
      reject(new StorageUploadError());
    };
    xhr.send(file);
  });
}
