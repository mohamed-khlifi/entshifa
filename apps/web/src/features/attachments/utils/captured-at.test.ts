import { describe, expect, it } from "vitest";

import {
  dateTimeLocalToUtcIso,
  nextClinicDayUtcIso,
  startOfClinicDayUtcIso,
} from "./captured-at";

describe("captured-at", () => {
  it("treats a UTC clinic day as an exclusive range", () => {
    expect(startOfClinicDayUtcIso("2026-09-27", "UTC")).toBe(
      "2026-09-27T00:00:00.000Z",
    );
    expect(nextClinicDayUtcIso("2026-09-27", "UTC")).toBe(
      "2026-09-28T00:00:00.000Z",
    );
  });

  it("converts a clinic-local capture time to UTC", () => {
    expect(dateTimeLocalToUtcIso("2026-09-27T10:30", "UTC")).toBe(
      "2026-09-27T10:30:00.000Z",
    );
    expect(dateTimeLocalToUtcIso("2026-09-27T00:00", "Europe/Paris")).toBe(
      "2026-09-26T22:00:00.000Z",
    );
    expect(dateTimeLocalToUtcIso("not-a-date", "UTC")).toBeNull();
  });
});
