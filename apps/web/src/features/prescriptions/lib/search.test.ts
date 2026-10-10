import { describe, expect, it } from "vitest";

import { templatesForVisit, catalogOnlyDrugs } from "./search";
import type {
  DrugRead,
  FormularyEntryRead,
  PrescriptionTemplateRead,
} from "@/lib/api/generated";

const FORMULARY = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
const DRUG = "01ARZ3NDEKTSV4RRFFQ69G5FAW";
const OTHER = "01ARZ3NDEKTSV4RRFFQ69G5FAX";

function template(
  code: string,
  complaints: string[],
): PrescriptionTemplateRead {
  return {
    publicId: FORMULARY,
    code,
    nameKey: `prescriptions.templates.${code}`,
    isPediatric: false,
    complaintConceptIds: complaints,
    items: [],
    version: 1,
  };
}

describe("templatesForVisit", () => {
  it("ranks complaint matches ahead of a search filter", () => {
    const ranked = templatesForVisit(
      [
        template("general_adult", []),
        template("ear_pain_child", ["complaint-ear"]),
      ],
      ["complaint-ear"],
      "",
    );
    expect(ranked.map((item) => item.code)).toEqual(["ear_pain_child"]);
  });

  it("keeps general templates when the visit has no matching favourite", () => {
    const ranked = templatesForVisit(
      [template("general_adult", [])],
      ["complaint-nose"],
      "general",
    );
    expect(ranked).toHaveLength(1);
  });
});

describe("catalogOnlyDrugs", () => {
  it("hides drugs already on the clinic formulary", () => {
    const drug = { publicId: DRUG } as DrugRead;
    const other = { publicId: OTHER } as DrugRead;
    const entry = { drug: { publicId: DRUG } } as FormularyEntryRead;
    expect(catalogOnlyDrugs([drug, other], [entry])).toEqual([other]);
  });
});
