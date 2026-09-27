import { cleanup, render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AttachmentUploadProgress } from "./AttachmentUploadProgress";

const messages = {
  attachments: {
    upload: {
      progress: "{percent}% · {loaded} / {total}",
      retry: "Retry",
      errors: {
        storage: "Storage did not accept the file. You can retry.",
      },
    },
  },
};

afterEach(() => {
  cleanup();
});

describe("AttachmentUploadProgress", () => {
  it("shows byte progress and a retry control after failure", () => {
    const onRetry = vi.fn();
    const view = render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <AttachmentUploadProgress
          phase="failed"
          loaded={20}
          total={100}
          loadedLabel="20 MB"
          totalLabel="100 MB"
          onRetry={onRetry}
        />
      </NextIntlClientProvider>,
    );

    const progress = view.getByTestId("attachments.upload.progress");
    expect(progress.textContent).toContain("20%");
    expect(progress.textContent).toContain("20 MB / 100 MB");
    view.getByTestId("attachments.upload.retry").click();
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("renders nothing before an upload starts", () => {
    const view = render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <AttachmentUploadProgress
          phase="idle"
          loaded={0}
          total={0}
          loadedLabel="0 B"
          totalLabel="0 B"
          onRetry={vi.fn()}
        />
      </NextIntlClientProvider>,
    );
    expect(view.queryByTestId("attachments.upload.progress")).toBeNull();
  });
});
