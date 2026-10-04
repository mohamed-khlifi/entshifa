import type {
  AnatomicalMapDefinition,
  MapRegionDefinition,
} from "@/lib/anatomy/types";

const level = {
  valueSetCode: "neck.level.findings",
  defaultNormalCode: "FIND.NECK.NORMAL",
} as const;

const salivary = {
  valueSetCode: "neck.salivary.findings",
  defaultNormalCode: "FIND.SALIVARY.NORMAL",
} as const;

function midline(
  region: Omit<MapRegionDefinition, "fixedLaterality">,
): MapRegionDefinition {
  return { ...region, fixedLaterality: "midline" };
}

export const neckLevelsMap: AnatomicalMapDefinition = {
  id: "neck-levels",
  paired: true,
  svg: "/anatomy/neck-levels.svg",
  titleKey: "maps.neckLevels",
  regions: [
    {
      id: "neck.parotid",
      pathId: "neck-parotid",
      labelKey: "neck.regions.parotid",
      bodySiteCode: "ANAT.PAROTID",
      ...salivary,
    },
    midline({
      id: "neck.level.ia",
      pathId: "neck-ia",
      labelKey: "neck.regions.levelIa",
      bodySiteCode: "ANAT.NECK.IA",
      ...level,
    }),
    {
      id: "neck.level.ib",
      pathId: "neck-ib",
      labelKey: "neck.regions.levelIb",
      bodySiteCode: "ANAT.NECK.IB",
      ...level,
    },
    {
      id: "neck.level.iia",
      pathId: "neck-iia",
      labelKey: "neck.regions.levelIia",
      bodySiteCode: "ANAT.NECK.IIA",
      ...level,
    },
    {
      id: "neck.level.iib",
      pathId: "neck-iib",
      labelKey: "neck.regions.levelIib",
      bodySiteCode: "ANAT.NECK.IIB",
      ...level,
    },
    {
      id: "neck.submandibular",
      pathId: "neck-smg",
      labelKey: "neck.regions.submandibular",
      bodySiteCode: "ANAT.SUBMANDIBULAR",
      ...salivary,
    },
    {
      id: "neck.level.iii",
      pathId: "neck-iii",
      labelKey: "neck.regions.levelIii",
      bodySiteCode: "ANAT.NECK.III",
      ...level,
    },
    {
      id: "neck.level.iv",
      pathId: "neck-iv",
      labelKey: "neck.regions.levelIv",
      bodySiteCode: "ANAT.NECK.IV",
      ...level,
    },
    {
      id: "neck.level.va",
      pathId: "neck-va",
      labelKey: "neck.regions.levelVa",
      bodySiteCode: "ANAT.NECK.VA",
      ...level,
    },
    {
      id: "neck.level.vb",
      pathId: "neck-vb",
      labelKey: "neck.regions.levelVb",
      bodySiteCode: "ANAT.NECK.VB",
      ...level,
    },
    midline({
      id: "neck.level.vi",
      pathId: "neck-vi",
      labelKey: "neck.regions.levelVi",
      bodySiteCode: "ANAT.NECK.VI",
      ...level,
    }),
    {
      id: "neck.thyroid-lobe",
      pathId: "neck-thyroid",
      labelKey: "neck.regions.thyroidLobe",
      bodySiteCode: "ANAT.THYROID.LOBE",
      valueSetCode: "neck.thyroid.findings",
      defaultNormalCode: "FIND.THYROID.NORMAL",
    },
    midline({
      id: "neck.isthmus",
      pathId: "neck-isthmus",
      labelKey: "neck.regions.isthmus",
      bodySiteCode: "ANAT.THYROID.ISTHMUS",
      valueSetCode: "neck.thyroid.findings",
      defaultNormalCode: "FIND.THYROID.NORMAL",
    }),
    midline({
      id: "neck.level.vii",
      pathId: "neck-vii",
      labelKey: "neck.regions.levelVii",
      bodySiteCode: "ANAT.NECK.VII",
      ...level,
    }),
  ],
};
