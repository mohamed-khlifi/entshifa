import { describe, expect, it } from "vitest";

import { isoToDateTimeLocal } from "./clock";

describe("otology clock", () => {
  it("reads a naive UTC instant the same way as an explicit Z", () => {
    expect(isoToDateTimeLocal("2026-10-11T16:39:00", "Europe/Paris")).toBe(
      isoToDateTimeLocal("2026-10-11T16:39:00Z", "Europe/Paris"),
    );
    expect(isoToDateTimeLocal("2026-10-11T16:39:00Z", "Europe/Paris")).toBe(
      "2026-10-11T18:39",
    );
  });
});
