import { describe, expect, it } from "vitest";

import {
  calculatorCatalogKey,
  calculatorMessageKey,
} from "@/features/calculators/lib/labels";

describe("calculatorMessageKey", () => {
  it("strips calculators namespace prefix", () => {
    expect(calculatorMessageKey("calculators.fields.percent")).toBe(
      "fields.percent",
    );
  });

  it("returns key unchanged when not prefixed", () => {
    expect(calculatorMessageKey("fields.percent")).toBe("fields.percent");
  });
});

describe("calculatorCatalogKey", () => {
  it("maps dotted codes to catalog keys", () => {
    expect(calculatorCatalogKey("endoscopy.lund_kennedy")).toBe(
      "catalog.endoscopy_lund_kennedy",
    );
  });
});
