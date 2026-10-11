import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";

import documents from "../../../../../../packages/i18n-messages/en/documents.json";
import { testIds } from "@/lib/test/test-id";

import { ImagingRequestForm } from "./ImagingRequestForm";

describe("ImagingRequestForm", () => {
  it("blocks MRI submit until an override reason is long enough", () => {
    const onSubmit = vi.fn();
    render(
      <NextIntlClientProvider locale="en" messages={{ documents }}>
        <ImagingRequestForm
          flagCodes={["cochlear_implant"]}
          suggestedQuestion="sudden hearing loss"
          pending={false}
          onSubmit={onSubmit}
          onClose={vi.fn()}
        />
      </NextIntlClientProvider>,
    );
    fireEvent.change(screen.getByTestId(testIds.documents.modality), {
      target: { value: "mri_iac_gadolinium" },
    });
    expect(screen.getByTestId(testIds.documents.mriWarning)).toBeTruthy();
    const submit = screen.getByTestId(testIds.documents.visitCreate);
    expect(submit.hasAttribute("disabled")).toBe(true);
    fireEvent.change(screen.getByTestId(testIds.documents.overrideReason), {
      target: { value: "Radiology confirmed a conditional implant" },
    });
    expect(submit.hasAttribute("disabled")).toBe(false);
    fireEvent.click(submit);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        modality: "mri_iac_gadolinium",
        overrideReason: "Radiology confirmed a conditional implant",
        contrastAllergy: false,
        renalImpairment: false,
      }),
    );
  });
});
