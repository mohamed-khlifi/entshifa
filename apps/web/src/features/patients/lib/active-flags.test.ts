import { describe, expect, it } from "vitest";

import { isFlagActive, splitHearingAlerts } from "../lib/active-flags";
import type { PatientFlagRead } from "@/lib/api/generated";

function flag(
  partial: Partial<PatientFlagRead> & Pick<PatientFlagRead, "flagCode">,
): PatientFlagRead {
  return {
    publicId: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    laterality: null,
    severity: null,
    detail: null,
    startedOn: "2020-01-01",
    endedOn: null,
    isAuto: false,
    recordedByPublicId: null,
    version: 1,
    ...partial,
  };
}

describe("patient safety flags", () => {
  const today = new Date(2026, 8, 27);

  it("treats an open flag as active", () => {
    expect(isFlagActive(flag({ flagCode: "diabetes" }), today)).toBe(true);
  });

  it("ends a flag on its end date", () => {
    expect(
      isFlagActive(
        flag({ flagCode: "pregnancy", endedOn: "2026-09-27" }),
        today,
      ),
    ).toBe(false);
  });

  it("keeps only hearing ear separate from other alerts", () => {
    const split = splitHearingAlerts([
      flag({ flagCode: "only_hearing_ear" }),
      flag({
        flagCode: "pacemaker",
        publicId: "01ARZ3NDEKTSV4RRFFQ69G5FAW",
      }),
      flag({
        flagCode: "diabetes",
        publicId: "01ARZ3NDEKTSV4RRFFQ69G5FAX",
        endedOn: "2020-01-02",
      }),
    ]);
    expect(split.onlyHearingEar).toHaveLength(1);
    expect(split.other.map((row) => row.flagCode)).toEqual(["pacemaker"]);
  });
});
