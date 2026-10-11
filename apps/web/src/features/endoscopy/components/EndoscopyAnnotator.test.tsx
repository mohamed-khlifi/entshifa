import { cleanup, fireEvent, render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";

import { testIds } from "@/lib/test/test-id";
import endoscopyMessages from "../../../../../../packages/i18n-messages/en/endoscopy.json";

import { EndoscopyAnnotator } from "./EndoscopyAnnotator";

vi.mock("@/lib/forms/autosave", () => ({
  readDraftSnapshot: async () => null,
  writeDraftSnapshot: async () => undefined,
}));

class TestPointerEvent extends MouseEvent {
  pointerId: number;

  constructor(
    type: string,
    init: MouseEventInit & { pointerId?: number } = {},
  ) {
    super(type, init);
    this.pointerId = init.pointerId ?? 1;
  }
}

describe("EndoscopyAnnotator", () => {
  beforeAll(() => {
    vi.stubGlobal("PointerEvent", TestPointerEvent);
  });

  afterEach(() => {
    cleanup();
  });

  it("draws an arrow on a separate layer and leaves the image source unchanged", () => {
    const imageUrl = "https://example.test/original.png";
    Element.prototype.getBoundingClientRect = () =>
      ({
        x: 0,
        y: 0,
        width: 100,
        height: 100,
        top: 0,
        left: 0,
        bottom: 100,
        right: 100,
        toJSON() {
          return {};
        },
      }) as DOMRect;
    const view = render(
      <NextIntlClientProvider
        locale="en"
        messages={{ endoscopy: endoscopyMessages }}
      >
        <EndoscopyAnnotator
          imageUrl={imageUrl}
          storageKey="endoscopy-annotation:01ARZ3NDEKTSV4RRFFQ69G5FB0"
          readOnly={false}
          onClose={() => undefined}
        />
      </NextIntlClientProvider>,
    );
    const image = view.getByTestId(testIds.endoscopy.annotateImage);
    fireEvent.click(view.getByTestId(testIds.endoscopy.toolArrow));
    const surface = view.getByTestId(testIds.endoscopy.annotateSurface);
    fireEvent.pointerDown(surface, { clientX: 10, clientY: 10, pointerId: 1 });
    fireEvent.pointerMove(surface, { clientX: 40, clientY: 50, pointerId: 1 });
    fireEvent.pointerUp(surface, { clientX: 40, clientY: 50, pointerId: 1 });
    expect(image.getAttribute("src")).toBe(imageUrl);
    const line = surface.querySelector("line");
    expect(line).not.toBeNull();
    expect(line?.getAttribute("x1")).toBe("10");
    expect(line?.getAttribute("y1")).toBe("10");
    expect(line?.getAttribute("x2")).toBe("40");
    expect(line?.getAttribute("y2")).toBe("50");
  });
});
