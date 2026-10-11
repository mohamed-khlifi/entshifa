import { fireEvent, render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";

import { RecallRowActions } from "./RecallRowActions";
import type { RecallRead } from "@/lib/api/generated";
import { recallActionTestId } from "@/lib/test/test-id";

const messages = {
  recalls: {
    actions: {
      book: "Book",
      call: "Call",
      cancel: "Cancel recall",
      email: "Email",
      sms: "SMS",
      unreachable: "Unreachable",
      whatsapp: "WhatsApp",
    },
  },
};

const recall = {
  publicId: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  version: 3,
} as RecallRead;

describe("RecallRowActions", () => {
  it("logs a call and marks the patient unreachable from the row", () => {
    const onContact = vi.fn();
    const onUnreachable = vi.fn();
    const view = render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <RecallRowActions
          recall={recall}
          disabled={false}
          onBook={vi.fn()}
          onContact={onContact}
          onUnreachable={onUnreachable}
          onCancel={vi.fn()}
        />
      </NextIntlClientProvider>,
    );

    fireEvent.click(
      view.getByTestId(recallActionTestId("call", recall.publicId)),
    );
    fireEvent.click(
      view.getByTestId(recallActionTestId("unreachable", recall.publicId)),
    );

    expect(onContact).toHaveBeenCalledWith(recall, "call");
    expect(onUnreachable).toHaveBeenCalledWith(recall);
  });
});
