/** Data-only description of a clickable examination map. */

export type MapSide = "right" | "left";

export type MapLaterality = MapSide | "midline";

export type MapRegionDefinition = {
  id: string;
  pathId: string;
  /** Key under the `examination` catalog, passed to `t()`. */
  labelKey: string;
  bodySiteCode: string;
  valueSetCode: string;
  defaultNormalCode: string;
  /** When set, the side toggle does not apply to this region. */
  fixedLaterality?: "midline";
};

export type AnatomicalMapDefinition = {
  id: string;
  paired: boolean;
  svg: string;
  titleKey: string;
  regions: readonly MapRegionDefinition[];
};

export type MapFindingOption = {
  code: string;
  display: string;
};

export type RegionMark = {
  status: "not_examined" | "normal" | "abnormal";
  conceptCode: string | null;
  dirty: boolean;
};
