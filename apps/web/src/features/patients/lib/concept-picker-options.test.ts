import { describe, expect, it } from "vitest";

import {
  conceptOptionsFromDictionary,
  filterConceptOptions,
} from "./concept-picker-options";

describe("filterConceptOptions", () => {
  const options = [
    { publicId: "01A", display: "Effusion" },
    { publicId: "01B", display: "Perforation" },
  ];

  it("returns all options when the query is empty", () => {
    expect(filterConceptOptions(options, "")).toEqual(options);
  });

  it("filters by display text case-insensitively", () => {
    expect(filterConceptOptions(options, "eff")).toEqual([options[0]]);
  });
});

describe("conceptOptionsFromDictionary", () => {
  it("sorts concepts by display label", () => {
    expect(
      conceptOptionsFromDictionary({
        a: { publicId: "01A", display: "Zebra" },
        b: { publicId: "01B", display: "Alpha" },
      }),
    ).toEqual([
      { publicId: "01B", display: "Alpha" },
      { publicId: "01A", display: "Zebra" },
    ]);
  });
});
