import type { ObservationCreate } from "@/lib/api/generated";

import type {
  AnatomicalMapDefinition,
  MapLaterality,
  MapRegionDefinition,
  MapSide,
  RegionMark,
} from "@/lib/anatomy/types";

export type NarrativeFindingDraft = {
  conceptCode: string;
  bodySiteCode: string;
  mapRegionCode: string;
  laterality: MapLaterality;
  status: RegionMark["status"];
  sortIndex: number;
};

export function regionStorageKey(
  laterality: MapLaterality,
  regionId: string,
): string {
  return `${laterality}:${regionId}`;
}

export function effectiveLaterality(
  region: MapRegionDefinition,
  selected: MapSide,
): MapLaterality {
  return region.fixedLaterality ?? selected;
}

export function markNormal(region: MapRegionDefinition): RegionMark {
  return {
    status: "normal",
    conceptCode: region.defaultNormalCode,
    dirty: true,
  };
}

export function markFinding(conceptCode: string): RegionMark {
  return {
    status: "abnormal",
    conceptCode,
    dirty: true,
  };
}

export function markNotExamined(): RegionMark {
  return {
    status: "not_examined",
    conceptCode: null,
    dirty: true,
  };
}

export function dirtyMarks(
  definition: AnatomicalMapDefinition,
  selected: MapSide,
  marks: Readonly<Record<string, RegionMark>>,
): Array<{
  region: MapRegionDefinition;
  laterality: MapLaterality;
  mark: RegionMark;
  sortIndex: number;
}> {
  const rows: Array<{
    region: MapRegionDefinition;
    laterality: MapLaterality;
    mark: RegionMark;
    sortIndex: number;
  }> = [];
  definition.regions.forEach((region, sortIndex) => {
    const laterality = effectiveLaterality(region, selected);
    const mark = marks[regionStorageKey(laterality, region.id)];
    if (!mark?.dirty) {
      return;
    }
    rows.push({ region, laterality, mark, sortIndex });
  });
  return rows;
}

export function toNarrativeDrafts(
  definition: AnatomicalMapDefinition,
  selected: MapSide,
  marks: Readonly<Record<string, RegionMark>>,
): NarrativeFindingDraft[] {
  return dirtyMarks(definition, selected, marks).map((row) => ({
    conceptCode: conceptCodeFor(row.region, row.mark),
    bodySiteCode: row.region.bodySiteCode,
    mapRegionCode: row.region.id,
    laterality: row.laterality,
    status: row.mark.status,
    sortIndex: row.sortIndex,
  }));
}

export function toObservationCreates(
  definition: AnatomicalMapDefinition,
  selected: MapSide,
  marks: Readonly<Record<string, RegionMark>>,
  effectiveAt: string,
): ObservationCreate[] {
  return dirtyMarks(definition, selected, marks).map((row) => {
    const conceptCode = conceptCodeFor(row.region, row.mark);
    return {
      conceptCode,
      bodySiteCode: row.region.bodySiteCode,
      mapRegionCode: row.region.id,
      laterality: row.laterality,
      status: row.mark.status,
      valueType: "code",
      valueConceptCode: conceptCode,
      effectiveAt,
      source: "clinician",
      confirmed: true,
      components: [],
    };
  });
}

function conceptCodeFor(region: MapRegionDefinition, mark: RegionMark): string {
  if (mark.status === "abnormal" && mark.conceptCode) {
    return mark.conceptCode;
  }
  return region.defaultNormalCode;
}
