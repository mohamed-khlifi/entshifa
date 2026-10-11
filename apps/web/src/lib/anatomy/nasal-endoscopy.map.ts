import type { AnatomicalMapDefinition } from "@/lib/anatomy/types";

const findings = {
  valueSetCode: "endoscopy.findings",
  defaultNormalCode: "FIND.ENDO.NORMAL",
} as const;

const midline = { fixedLaterality: "midline" as const };

/** Passage order from feature spec section 7.1. Office rhinoscopy stays a separate map. */
export const nasalEndoscopyMap: AnatomicalMapDefinition = {
  id: "nasal-endoscopy",
  paired: true,
  svg: "/anatomy/nasal-endoscopy.svg",
  titleKey: "maps.nasalEndoscopy",
  regions: [
    {
      id: "endo.vestibule",
      pathId: "endo-vestibule",
      labelKey: "endo.regions.vestibule",
      bodySiteCode: "ANAT.NASAL.VESTIBULE",
      ...findings,
    },
    {
      id: "endo.valve",
      pathId: "endo-valve",
      labelKey: "endo.regions.valve",
      bodySiteCode: "ANAT.NASAL.VALVE",
      ...findings,
    },
    {
      id: "endo.septum",
      pathId: "endo-septum",
      labelKey: "endo.regions.septum",
      bodySiteCode: "ANAT.NASAL.SEPTUM",
      ...findings,
      ...midline,
    },
    {
      id: "endo.inferior-turbinate",
      pathId: "endo-inferior-turbinate",
      labelKey: "endo.regions.inferiorTurbinate",
      bodySiteCode: "ANAT.NASAL.INFERIOR_TURBINATE",
      ...findings,
    },
    {
      id: "endo.inferior-meatus",
      pathId: "endo-inferior-meatus",
      labelKey: "endo.regions.inferiorMeatus",
      bodySiteCode: "ANAT.NASAL.INFERIOR_MEATUS",
      ...findings,
    },
    {
      id: "endo.middle-turbinate",
      pathId: "endo-middle-turbinate",
      labelKey: "endo.regions.middleTurbinate",
      bodySiteCode: "ANAT.NASAL.MIDDLE_TURBINATE",
      ...findings,
    },
    {
      id: "endo.middle-meatus",
      pathId: "endo-middle-meatus",
      labelKey: "endo.regions.middleMeatus",
      bodySiteCode: "ANAT.NASAL.MIDDLE_MEATUS",
      ...findings,
    },
    {
      id: "endo.uncinate",
      pathId: "endo-uncinate",
      labelKey: "endo.regions.uncinate",
      bodySiteCode: "ANAT.NASAL.UNCINATE",
      ...findings,
    },
    {
      id: "endo.bulla",
      pathId: "endo-bulla",
      labelKey: "endo.regions.bulla",
      bodySiteCode: "ANAT.NASAL.BULLA",
      ...findings,
    },
    {
      id: "endo.superior-turbinate",
      pathId: "endo-superior-turbinate",
      labelKey: "endo.regions.superiorTurbinate",
      bodySiteCode: "ANAT.NASAL.SUPERIOR_TURBINATE",
      ...findings,
    },
    {
      id: "endo.superior-meatus",
      pathId: "endo-superior-meatus",
      labelKey: "endo.regions.superiorMeatus",
      bodySiteCode: "ANAT.NASAL.SUPERIOR_MEATUS",
      ...findings,
    },
    {
      id: "endo.sphenoethmoidal-recess",
      pathId: "endo-sphenoethmoidal-recess",
      labelKey: "endo.regions.sphenoethmoidalRecess",
      bodySiteCode: "ANAT.NASAL.SPHENOETHMOIDAL_RECESS",
      ...findings,
    },
    {
      id: "endo.olfactory-cleft",
      pathId: "endo-olfactory-cleft",
      labelKey: "endo.regions.olfactoryCleft",
      bodySiteCode: "ANAT.NASAL.OLFACTORY_CLEFT",
      ...findings,
    },
    {
      id: "endo.nasopharynx",
      pathId: "endo-nasopharynx",
      labelKey: "endo.regions.nasopharynx",
      bodySiteCode: "ANAT.NASAL.NASOPHARYNX",
      ...findings,
      ...midline,
    },
    {
      id: "endo.post-fess",
      pathId: "endo-post-fess",
      labelKey: "endo.regions.postFess",
      bodySiteCode: "ANAT.NASAL.POST_FESS",
      ...findings,
      ...midline,
    },
  ],
};
