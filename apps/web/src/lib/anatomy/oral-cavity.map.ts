import type { AnatomicalMapDefinition } from "@/lib/anatomy/types";

const oral = {
  valueSetCode: "oral.findings",
  defaultNormalCode: "FIND.ORAL.NORMAL",
  fixedLaterality: "midline" as const,
};

export const oralCavityMap: AnatomicalMapDefinition = {
  id: "oral-cavity",
  paired: true,
  svg: "/anatomy/oral-cavity.svg",
  titleKey: "maps.oralCavity",
  regions: [
    {
      id: "oral.lips",
      pathId: "oral-lips",
      labelKey: "oral.regions.lips",
      bodySiteCode: "ANAT.ORAL.LIPS",
      ...oral,
    },
    {
      id: "oral.tongue",
      pathId: "oral-tongue",
      labelKey: "oral.regions.tongue",
      bodySiteCode: "ANAT.ORAL.TONGUE",
      ...oral,
    },
    {
      id: "oral.soft-palate",
      pathId: "oral-palate",
      labelKey: "oral.regions.softPalate",
      bodySiteCode: "ANAT.ORAL.SOFT_PALATE",
      ...oral,
    },
    {
      id: "oral.tonsil",
      pathId: "oral-tonsil",
      labelKey: "oral.regions.tonsil",
      bodySiteCode: "ANAT.ORAL.TONSIL",
      valueSetCode: "oral.tonsil.findings",
      defaultNormalCode: "FIND.TONSIL.NORMAL",
    },
    {
      id: "oral.posterior-wall",
      pathId: "oral-ppw",
      labelKey: "oral.regions.posteriorWall",
      bodySiteCode: "ANAT.ORAL.POSTERIOR_WALL",
      ...oral,
    },
  ],
};
