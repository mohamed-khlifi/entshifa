import { cleanup, fireEvent, render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { laryngoscopyLesionCellTestId } from "@/lib/test/test-id";
import laryngoscopyMessages from "../../../../../../packages/i18n-messages/en/laryngoscopy.json";

import { VocalFoldDiagram } from "./VocalFoldDiagram";

afterEach(() => {
  cleanup();
});

describe("VocalFoldDiagram", () => {
  it("places a lesion with laterality, third and surface", () => {
    const onAdd = vi.fn();
    const view = render(
      <NextIntlClientProvider
        locale="en"
        messages={{ laryngoscopy: laryngoscopyMessages }}
      >
        <VocalFoldDiagram
          lesions={[]}
          thirds={[
            {
              publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB6",
              code: "QUAL.VF.THIRD.ANTERIOR",
              kind: "qualifier",
              display: "Anterior",
              locale: "en",
              translationMissing: false,
            },
          ]}
          surfaces={[
            {
              publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB7",
              code: "QUAL.VF.SURFACE.FREE_EDGE",
              kind: "qualifier",
              display: "Free edge",
              locale: "en",
              translationMissing: false,
            },
          ]}
          findings={[
            {
              publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB8",
              code: "FIND.LARYNX.NODULE",
              kind: "finding",
              display: "Nodule",
              locale: "en",
              translationMissing: false,
            },
          ]}
          reinkeCode="FIND.LARYNX.REINKE_EDEMA"
          reinkeGrades={[1, 2, 3]}
          readOnly={false}
          onAdd={onAdd}
          onChange={() => undefined}
          onRemove={() => undefined}
        />
      </NextIntlClientProvider>,
    );
    fireEvent.click(
      view.getByTestId(
        laryngoscopyLesionCellTestId(
          "right",
          "QUAL.VF.THIRD.ANTERIOR",
          "QUAL.VF.SURFACE.FREE_EDGE",
        ),
      ),
    );
    expect(onAdd).toHaveBeenCalledWith({
      laterality: "right",
      thirdCode: "QUAL.VF.THIRD.ANTERIOR",
      surfaceCode: "QUAL.VF.SURFACE.FREE_EDGE",
      findingCode: "FIND.LARYNX.NODULE",
      sizeMm: null,
      reinkeGrade: null,
    });
  });
});
