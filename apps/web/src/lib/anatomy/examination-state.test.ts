import { describe, expect, it } from "vitest";

import { oralCavityMap } from "@/lib/anatomy/oral-cavity.map";
import {
  markFinding,
  markFromFinding,
  markNormal,
  regionStorageKey,
  toObservationCreates,
} from "@/lib/anatomy/examination-state";

const at = "2026-06-01T09:00:00.000Z";

describe("markFromFinding", () => {
  it("records the normal concept as normal and any other concept as abnormal", () => {
    const tonsil = oralCavityMap.regions.find(
      (region) => region.id === "oral.tonsil",
    );
    expect(tonsil).toBeDefined();
    if (!tonsil) {
      return;
    }
    expect(markFromFinding(tonsil, tonsil.defaultNormalCode).status).toBe(
      "normal",
    );
    expect(markFromFinding(tonsil, "FIND.TONSIL.BRODSKY_2").status).toBe(
      "abnormal",
    );
  });
});

describe("toObservationCreates", () => {
  it("writes a tonsil grade on the selected side", () => {
    const tonsil = oralCavityMap.regions.find(
      (region) => region.id === "oral.tonsil",
    );
    expect(tonsil).toBeDefined();
    if (!tonsil) {
      return;
    }
    const rows = toObservationCreates(
      oralCavityMap,
      "right",
      {
        [regionStorageKey("right", tonsil.id)]: markFinding(
          "FIND.TONSIL.BRODSKY_2",
        ),
      },
      at,
    );
    expect(rows).toEqual([
      {
        conceptCode: "FIND.TONSIL.BRODSKY_2",
        bodySiteCode: "ANAT.ORAL.TONSIL",
        mapRegionCode: "oral.tonsil",
        laterality: "right",
        status: "abnormal",
        valueType: "code",
        valueConceptCode: "FIND.TONSIL.BRODSKY_2",
        effectiveAt: at,
        source: "clinician",
        confirmed: true,
        components: [],
      },
    ]);
  });

  it("keeps a midline structure off the side toggle", () => {
    const lips = oralCavityMap.regions.find(
      (region) => region.id === "oral.lips",
    );
    expect(lips).toBeDefined();
    if (!lips) {
      return;
    }
    const rows = toObservationCreates(
      oralCavityMap,
      "left",
      { [regionStorageKey("midline", lips.id)]: markNormal(lips) },
      at,
    );
    expect(rows[0]?.laterality).toBe("midline");
    expect(rows[0]?.conceptCode).toBe("FIND.ORAL.NORMAL");
    expect(rows[0]?.bodySiteCode).toBe("ANAT.ORAL.LIPS");
    expect(rows[0]?.mapRegionCode).toBe("oral.lips");
  });
});
