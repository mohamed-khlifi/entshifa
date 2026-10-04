import type {
  ExaminationSnapshotRead,
  ObservationCreate,
  ObservationRead,
} from "@/lib/api/generated";

import type {
  AnatomicalMapDefinition,
  MapLaterality,
  MapRegionDefinition,
  MapSide,
  MapState,
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

const MAP_SORT_STRIDE = 1000;

type MarkRow = {
  region: MapRegionDefinition;
  laterality: MapLaterality;
  mark: RegionMark;
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

export function isUntouchedCopy(mark: RegionMark): boolean {
  return mark.copied === true && mark.confirmed !== true;
}

export function markNormal(region: MapRegionDefinition): RegionMark {
  return clinicianMark("normal", region.defaultNormalCode);
}

export function markFinding(conceptCode: string): RegionMark {
  return clinicianMark("abnormal", conceptCode);
}

export function markFromFinding(
  region: MapRegionDefinition,
  conceptCode: string,
): RegionMark {
  if (conceptCode === region.defaultNormalCode) {
    return markNormal(region);
  }
  return markFinding(conceptCode);
}

export function markNotExamined(): RegionMark {
  return clinicianMark("not_examined", null);
}

export function markAllNormal(
  maps: readonly AnatomicalMapDefinition[],
): Record<string, MapState> {
  const next: Record<string, MapState> = {};
  for (const definition of maps) {
    next[definition.id] = {
      side: "right",
      marks: markSectionNormal(definition),
    };
  }
  return next;
}

export function markSectionNormal(
  definition: AnatomicalMapDefinition,
  side?: MapSide,
): Record<string, RegionMark> {
  const sides: MapSide[] = side
    ? [side]
    : definition.paired
      ? ["right", "left"]
      : ["right"];
  const marks: Record<string, RegionMark> = {};
  for (const selected of sides) {
    for (const region of definition.regions) {
      const laterality = effectiveLaterality(region, selected);
      if (side && laterality !== side) {
        continue;
      }
      marks[regionStorageKey(laterality, region.id)] = markNormal(region);
    }
  }
  return marks;
}

export function confirmMark(mark: RegionMark): RegionMark {
  return {
    status: mark.status,
    conceptCode: mark.conceptCode,
    dirty: true,
    copied: false,
    confirmed: true,
  };
}

export function confirmAllMarks(
  marks: Readonly<Record<string, RegionMark>>,
): Record<string, RegionMark> {
  const next: Record<string, RegionMark> = {};
  for (const [key, mark] of Object.entries(marks)) {
    next[key] = isUntouchedCopy(mark) ? confirmMark(mark) : mark;
  }
  return next;
}

export function hasUnconfirmedCopies(
  byMap: Readonly<Record<string, MapState>>,
): boolean {
  return Object.values(byMap).some((state) =>
    Object.values(state.marks).some((mark) => isUntouchedCopy(mark)),
  );
}

export function dirtyMarks(
  definition: AnatomicalMapDefinition,
  selected: MapSide,
  marks: Readonly<Record<string, RegionMark>>,
): MarkRow[] {
  const rows: MarkRow[] = [];
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
  return dirtyMarks(definition, selected, marks).map((row) =>
    toDraft(row.region, row.laterality, row.mark, row.sortIndex),
  );
}

export function toFullNarrativeDrafts(
  maps: readonly AnatomicalMapDefinition[],
  byMap: Readonly<Record<string, MapState>>,
): NarrativeFindingDraft[] {
  return dirtyRows(maps, byMap).map((row) =>
    toDraft(row.region, row.laterality, row.mark, row.sortIndex),
  );
}

export function toObservationCreates(
  definition: AnatomicalMapDefinition,
  selected: MapSide,
  marks: Readonly<Record<string, RegionMark>>,
  effectiveAt: string,
): ObservationCreate[] {
  return dirtyMarks(definition, selected, marks).map((row) =>
    toObservation(row, effectiveAt),
  );
}

export function toAllObservationCreates(
  maps: readonly AnatomicalMapDefinition[],
  byMap: Readonly<Record<string, MapState>>,
  effectiveAt: string,
): ObservationCreate[] {
  return dirtyRows(maps, byMap).map((row) => toObservation(row, effectiveAt));
}

export function hasDirtyExamination(
  maps: readonly AnatomicalMapDefinition[],
  byMap: Readonly<Record<string, MapState>>,
): boolean {
  return dirtyRows(maps, byMap).length > 0;
}

export function hydrateMarksFromObservations(
  maps: readonly AnatomicalMapDefinition[],
  observations: readonly ObservationRead[],
  sourceEncounterId: string,
): Record<string, MapState> {
  const regions = indexRegions(maps);
  const byMap: Record<string, MapState> = {};
  for (const observation of observations) {
    const regionId = observation.mapRegionCode;
    if (!regionId) {
      continue;
    }
    const located = regions.get(regionId);
    if (!located) {
      continue;
    }
    const status = observationStatus(observation.status);
    const conceptCode = conceptCodeFromObservation(
      observation,
      located.region,
      status,
    );
    if (conceptCode === undefined) {
      continue;
    }
    const state = byMap[located.definition.id] ?? {
      side: "right" as const,
      marks: {},
    };
    for (const laterality of lateralitiesFor(
      located.region,
      observation.laterality,
    )) {
      const key = regionStorageKey(laterality, located.region.id);
      if (state.marks[key]) {
        continue;
      }
      state.marks[key] = copiedMark(status, conceptCode, sourceEncounterId);
    }
    byMap[located.definition.id] = state;
  }
  return byMap;
}

export function hydrateMarksFromSnapshot(
  payload: unknown,
  sourceEncounterId: string,
): MapState | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const record = payload as Record<string, unknown>;
  const side = record.side === "left" ? "left" : "right";
  if (!record.marks || typeof record.marks !== "object") {
    return null;
  }
  const marks: Record<string, RegionMark> = {};
  for (const [key, value] of Object.entries(record.marks)) {
    const parsed = parseStoredMark(value);
    if (!parsed) {
      continue;
    }
    marks[key] = copiedMark(
      parsed.status,
      parsed.conceptCode,
      sourceEncounterId,
    );
  }
  if (Object.keys(marks).length === 0) {
    return null;
  }
  return { side, marks };
}

export function hydrateMarksFromSnapshots(
  maps: readonly AnatomicalMapDefinition[],
  snapshots: readonly ExaminationSnapshotRead[],
  sourceEncounterId: string,
): Record<string, MapState> {
  const known = new Set(maps.map((definition) => definition.id));
  const byMap: Record<string, MapState> = {};
  for (const snapshot of snapshots) {
    if (snapshot.encounterPublicId !== sourceEncounterId) {
      continue;
    }
    if (!known.has(snapshot.mapId) || byMap[snapshot.mapId]) {
      continue;
    }
    const state = hydrateMarksFromSnapshot(snapshot.payload, sourceEncounterId);
    if (state) {
      byMap[snapshot.mapId] = state;
    }
  }
  return byMap;
}

export function examinationStateFromCopy(
  maps: readonly AnatomicalMapDefinition[],
  observations: readonly ObservationRead[],
  snapshots: readonly ExaminationSnapshotRead[],
  sourceEncounterId: string,
): Record<string, MapState> {
  const fromObservations = hydrateMarksFromObservations(
    maps,
    observations,
    sourceEncounterId,
  );
  if (countMarks(fromObservations) > 0) {
    return fromObservations;
  }
  return hydrateMarksFromSnapshots(maps, snapshots, sourceEncounterId);
}

function clinicianMark(
  status: RegionMark["status"],
  conceptCode: string | null,
): RegionMark {
  return {
    status,
    conceptCode,
    dirty: true,
    copied: false,
    confirmed: true,
  };
}

function copiedMark(
  status: RegionMark["status"],
  conceptCode: string | null,
  sourceEncounterId: string,
): RegionMark {
  return {
    status,
    conceptCode,
    dirty: true,
    copied: true,
    confirmed: false,
    sourceEncounterId,
  };
}

function dirtyRows(
  maps: readonly AnatomicalMapDefinition[],
  byMap: Readonly<Record<string, MapState>>,
): MarkRow[] {
  const rows: MarkRow[] = [];
  maps.forEach((definition, mapIndex) => {
    const marks = byMap[definition.id]?.marks;
    if (!marks) {
      return;
    }
    const sides: MapSide[] = definition.paired ? ["right", "left"] : ["right"];
    const seen = new Set<string>();
    for (const selected of sides) {
      definition.regions.forEach((region, regionIndex) => {
        const laterality = effectiveLaterality(region, selected);
        const key = regionStorageKey(laterality, region.id);
        if (seen.has(key)) {
          return;
        }
        seen.add(key);
        const mark = marks[key];
        if (!mark?.dirty) {
          return;
        }
        rows.push({
          region,
          laterality,
          mark,
          sortIndex: mapIndex * MAP_SORT_STRIDE + regionIndex,
        });
      });
    }
  });
  return rows;
}

function toDraft(
  region: MapRegionDefinition,
  laterality: MapLaterality,
  mark: RegionMark,
  sortIndex: number,
): NarrativeFindingDraft {
  return {
    conceptCode: conceptCodeFor(region, mark),
    bodySiteCode: region.bodySiteCode,
    mapRegionCode: region.id,
    laterality,
    status: mark.status,
    sortIndex,
  };
}

function toObservation(row: MarkRow, effectiveAt: string): ObservationCreate {
  const conceptCode = conceptCodeFor(row.region, row.mark);
  const observation: ObservationCreate = {
    conceptCode,
    bodySiteCode: row.region.bodySiteCode,
    mapRegionCode: row.region.id,
    laterality: row.laterality,
    status: row.mark.status,
    valueType: "code",
    valueConceptCode: conceptCode,
    effectiveAt,
    source: "clinician",
    confirmed: !isUntouchedCopy(row.mark),
    components: [],
  };
  const qualifiers = copyQualifiers(row.mark);
  if (qualifiers) {
    observation.qualifiers = qualifiers;
  }
  return observation;
}

function copyQualifiers(mark: RegionMark): ObservationCreate["qualifiers"] {
  if (!isUntouchedCopy(mark) || !mark.sourceEncounterId) {
    return undefined;
  }
  // Generated OpenAPI types model free-form qualifier objects as
  // Record<string, never>. The API accepts a string-keyed JSON object.
  const qualifiers: { copied: true; sourceEncounterPublicId: string } = {
    copied: true,
    sourceEncounterPublicId: mark.sourceEncounterId,
  };
  return qualifiers as unknown as ObservationCreate["qualifiers"];
}

function conceptCodeFor(region: MapRegionDefinition, mark: RegionMark): string {
  if (mark.status === "abnormal" && mark.conceptCode) {
    return mark.conceptCode;
  }
  return region.defaultNormalCode;
}

function indexRegions(
  maps: readonly AnatomicalMapDefinition[],
): Map<
  string,
  { definition: AnatomicalMapDefinition; region: MapRegionDefinition }
> {
  const indexed = new Map<
    string,
    { definition: AnatomicalMapDefinition; region: MapRegionDefinition }
  >();
  for (const definition of maps) {
    for (const region of definition.regions) {
      indexed.set(region.id, { definition, region });
    }
  }
  return indexed;
}

function observationStatus(value: string): RegionMark["status"] {
  if (value === "normal" || value === "abnormal" || value === "not_examined") {
    return value;
  }
  return "not_examined";
}

function conceptCodeFromObservation(
  observation: ObservationRead,
  region: MapRegionDefinition,
  status: RegionMark["status"],
): string | null | undefined {
  const coded =
    observation.valueConcept?.code ?? observation.concept.code ?? null;
  if (coded) {
    return coded;
  }
  if (status === "normal") {
    return region.defaultNormalCode;
  }
  if (status === "not_examined") {
    return null;
  }
  return undefined;
}

function lateralitiesFor(
  region: MapRegionDefinition,
  raw: string,
): MapLaterality[] {
  if (region.fixedLaterality) {
    return raw === region.fixedLaterality ? [region.fixedLaterality] : [];
  }
  if (raw === "right" || raw === "left") {
    return [raw];
  }
  if (raw === "bilateral") {
    return ["right", "left"];
  }
  return [];
}

function parseStoredMark(
  value: unknown,
): Pick<RegionMark, "status" | "conceptCode"> | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const mark = value as Record<string, unknown>;
  if (
    mark.status !== "not_examined" &&
    mark.status !== "normal" &&
    mark.status !== "abnormal"
  ) {
    return null;
  }
  if (mark.conceptCode !== null && typeof mark.conceptCode !== "string") {
    return null;
  }
  return {
    status: mark.status,
    conceptCode: mark.conceptCode,
  };
}

function countMarks(byMap: Readonly<Record<string, MapState>>): number {
  return Object.values(byMap).reduce(
    (total, state) => total + Object.keys(state.marks).length,
    0,
  );
}
