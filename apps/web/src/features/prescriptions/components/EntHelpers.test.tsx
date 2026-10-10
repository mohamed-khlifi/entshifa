import { fireEvent, render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";

import { EntHelpers } from "./EntHelpers";
import { testIds } from "@/lib/test/test-id";

const messages = {
  prescriptions: {
    helpers: {
      title: "Technique notes",
      saline: "Saline",
      salineVolume: "Volume",
      salineFrequency: "Times per day",
      salineApply: "Add irrigation",
      salineText:
        "Wash {volume} {frequency, plural, one {# time} other {# times}}",
      spray: "Spray",
      sprayApply: "Add spray",
      sprayText: "Aim away from the septum.",
      drops: "Drops",
      dropsApply: "Add drops",
      dropsText: "Press the tragus.",
      taper: "Taper",
      taperStart: "Start",
      taperStep: "Step",
      taperDays: "Days",
      taperFloor: "Floor",
      taperPreview: "Preview",
      taperApply: "Attach",
      taperCount: "{count, plural, one {# day} other {# days}}",
      taperDay: "Day {day}: {dose} mg",
    },
  },
};

describe("EntHelpers", () => {
  it("inserts the spray technique and a clinician-entered irrigation note", () => {
    const onAppend = vi.fn();
    const view = render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <EntHelpers
          disabled={false}
          schedule={[]}
          onAppend={onAppend}
          onPreviewTaper={vi.fn()}
          onApplyTaper={vi.fn()}
        />
      </NextIntlClientProvider>,
    );
    fireEvent.click(view.getByTestId(testIds.prescriptions.sprayApply));
    expect(onAppend).toHaveBeenCalledWith("Aim away from the septum.");
    fireEvent.change(view.getByTestId(testIds.prescriptions.salineVolume), {
      target: { value: "120 mL" },
    });
    fireEvent.change(view.getByTestId(testIds.prescriptions.salineFrequency), {
      target: { value: "2" },
    });
    fireEvent.click(view.getByTestId(testIds.prescriptions.salineApply));
    expect(onAppend).toHaveBeenLastCalledWith("Wash 120 mL 2 times");
  });
});
