import { describe, expect, it } from "vitest";

import type {
  ExaminationSnapshotRead,
  ObservationRead,
} from "@/lib/api/generated";
import { anatomicalMaps } from "@/lib/anatomy";
import { nasalCavityMap } from "@/lib/anatomy/nasal-cavity.map";
import { neckLevelsMap } from "@/lib/anatomy/neck-levels.map";
import { oralCavityMap } from "@/lib/anatomy/oral-cavity.map";
import { tympanicMembraneMap } from "@/lib/anatomy/tympanic-membrane.map";
import {
  confirmAllMarks,
  confirmMark,
  examinationStateFromCopy,
  hasUnconfirmedCopies,
  hydrateMarksFromObservations,
  hydrateMarksFromSnapshot,
  isUntouchedCopy,
  markAllNormal,
  markFinding,
  markFromFinding,
  markNormal,
  markSectionNormal,
  regionStorageKey,
  toAllObservationCreates,
  toFullNarrativeDrafts,
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

describe("one-click normals", () => {
  it("marks every region of every map, both sides, as a confirmed normal", () => {
    const byMap = markAllNormal(anatomicalMaps);
    const drafts = toFullNarrativeDrafts(anatomicalMaps, byMap);
    expect(drafts).toHaveLength(54);
    expect(drafts.every((row) => row.status === "normal")).toBe(true);
    expect(
      drafts.map((row) => `${row.laterality}:${row.mapRegionCode}`),
    ).toEqual(
      expect.arrayContaining([
        "right:tm.canal",
        "left:tm.canal",
        "right:nose.septum",
        "left:nose.septum",
        "midline:oral.lips",
        "right:oral.tonsil",
        "left:oral.tonsil",
        "midline:neck.level.ia",
        "right:neck.parotid",
        "left:neck.parotid",
      ]),
    );
    const canal = drafts.find((row) => row.mapRegionCode === "tm.canal");
    const septum = drafts.find((row) => row.mapRegionCode === "nose.septum");
    expect(canal?.sortIndex).toBe(0);
    expect((septum?.sortIndex ?? 0) > (canal?.sortIndex ?? 0)).toBe(true);
    expect(hasUnconfirmedCopies(byMap)).toBe(false);
    const saved = toAllObservationCreates(anatomicalMaps, byMap, at);
    expect(saved).toHaveLength(54);
    expect(
      saved.every((row) => row.confirmed && row.qualifiers === undefined),
    ).toBe(true);
  });

  it("marks one side of otoscopy without the other side or other maps", () => {
    const marks = markSectionNormal(tympanicMembraneMap, "right");
    expect(Object.keys(marks)).toHaveLength(tympanicMembraneMap.regions.length);
    expect(Object.keys(marks).every((key) => key.startsWith("right:"))).toBe(
      true,
    );
    expect(marks[regionStorageKey("left", "tm.canal")]).toBeUndefined();
    const neck = markSectionNormal(neckLevelsMap, "right");
    expect(neck[regionStorageKey("midline", "neck.level.ia")]).toBeUndefined();
    expect(neck[regionStorageKey("right", "neck.parotid")]?.status).toBe(
      "normal",
    );
    expect(neck[regionStorageKey("left", "neck.parotid")]).toBeUndefined();
  });
});

describe("copy forward provenance", () => {
  const source = "01SOURCEENCOUNTER0000000000";

  it("saves an untouched copy as unconfirmed with a copied qualifier", () => {
    const canal = tympanicMembraneMap.regions[0];
    expect(canal).toBeDefined();
    if (!canal) {
      return;
    }
    const copied = {
      ...markFinding("FIND.CANAL.WAX"),
      copied: true,
      confirmed: false,
      sourceEncounterId: source,
    };
    expect(isUntouchedCopy(copied)).toBe(true);
    const rows = toAllObservationCreates(
      [tympanicMembraneMap],
      {
        [tympanicMembraneMap.id]: {
          side: "right",
          marks: { [regionStorageKey("right", canal.id)]: copied },
        },
      },
      at,
    );
    expect(rows[0]?.confirmed).toBe(false);
    expect(rows[0]?.qualifiers).toEqual({
      copied: true,
      sourceEncounterPublicId: source,
    });
  });

  it("drops the copied qualifier once the clinician confirms", () => {
    const canal = tympanicMembraneMap.regions[0];
    expect(canal).toBeDefined();
    if (!canal) {
      return;
    }
    const marks = confirmAllMarks({
      [regionStorageKey("right", canal.id)]: {
        ...markFinding("FIND.CANAL.WAX"),
        copied: true,
        confirmed: false,
        sourceEncounterId: source,
      },
    });
    const mark = marks[regionStorageKey("right", canal.id)];
    expect(mark && confirmMark(mark).confirmed).toBe(true);
    const rows = toObservationCreates(tympanicMembraneMap, "right", marks, at);
    expect(rows[0]?.confirmed).toBe(true);
    expect(rows[0]?.qualifiers).toBeUndefined();
    expect(rows[0]?.conceptCode).toBe("FIND.CANAL.WAX");
  });

  it("hydrates map observations and falls back to the newest snapshot", () => {
    const fromObservations = hydrateMarksFromObservations(
      anatomicalMaps,
      [observation("tm.canal", "right", "abnormal", "FIND.CANAL.WAX")],
      source,
    );
    const mark =
      fromObservations[tympanicMembraneMap.id]?.marks[
        regionStorageKey("right", "tm.canal")
      ];
    expect(mark).toMatchObject({
      status: "abnormal",
      conceptCode: "FIND.CANAL.WAX",
      dirty: true,
      copied: true,
      confirmed: false,
      sourceEncounterId: source,
    });

    const snapshot = hydrateMarksFromSnapshot(
      {
        side: "left",
        marks: {
          [regionStorageKey("left", "nose.septum")]: {
            status: "normal",
            conceptCode: "FIND.NOSE.NORMAL",
            dirty: false,
          },
        },
      },
      source,
    );
    expect(snapshot?.side).toBe("left");
    expect(
      snapshot?.marks[regionStorageKey("left", "nose.septum")]?.copied,
    ).toBe(true);

    const chosen = examinationStateFromCopy(
      anatomicalMaps,
      [],
      [
        snapshotRead("other-encounter", nasalCavityMap.id, {
          side: "right",
          marks: {
            [regionStorageKey("right", "nose.vestibule")]: markNormal(
              nasalCavityMap.regions[0]!,
            ),
          },
        }),
        snapshotRead(source, nasalCavityMap.id, {
          side: "left",
          marks: {
            [regionStorageKey("left", "nose.septum")]: {
              status: "abnormal",
              conceptCode: "FIND.NOSE.DEVIATION",
              dirty: true,
            },
          },
        }),
        snapshotRead(source, nasalCavityMap.id, {
          side: "right",
          marks: {
            [regionStorageKey("right", "nose.vestibule")]: {
              status: "normal",
              conceptCode: "FIND.NOSE.NORMAL",
              dirty: true,
            },
          },
        }),
      ],
      source,
    );
    expect(
      chosen[nasalCavityMap.id]?.marks[regionStorageKey("left", "nose.septum")]
        ?.conceptCode,
    ).toBe("FIND.NOSE.DEVIATION");
    expect(
      chosen[nasalCavityMap.id]?.marks[
        regionStorageKey("right", "nose.vestibule")
      ],
    ).toBeUndefined();
    expect(hydrateMarksFromSnapshot({ side: "right" }, source)).toBeNull();
  });
});

function observation(
  regionId: string,
  laterality: string,
  status: string,
  code: string,
): ObservationRead {
  return {
    publicId: "01OBSERVATION0000000000000",
    patientPublicId: "01PATIENT00000000000000000",
    encounterPublicId: "01SOURCEENCOUNTER0000000000",
    concept: { conceptId: "01CONCEPT0000000000000000", code, display: code },
    valueConcept: {
      conceptId: "01CONCEPT0000000000000000",
      code,
      display: code,
    },
    bodySite: null,
    mapRegionCode: regionId,
    laterality,
    status,
    valueType: "code",
    effectiveAt: at,
    source: "clinician",
    components: [],
    version: 1,
  };
}

function snapshotRead(
  encounterPublicId: string,
  mapId: string,
  payload: {
    side: string;
    marks: Record<string, unknown>;
  },
): ExaminationSnapshotRead {
  return {
    publicId: `01SNAPSHOT${mapId}`.slice(0, 26),
    patientPublicId: "01PATIENT00000000000000000",
    encounterPublicId,
    mapId,
    laterality: payload.side,
    payload: payload as unknown as ExaminationSnapshotRead["payload"],
    version: 1,
  };
}
