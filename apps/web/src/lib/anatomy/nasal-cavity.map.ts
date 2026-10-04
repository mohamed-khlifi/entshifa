import type { AnatomicalMapDefinition } from "@/lib/anatomy/types";

const nose = {
  valueSetCode: "nose.findings",
  defaultNormalCode: "FIND.NOSE.NORMAL",
} as const;

export const nasalCavityMap: AnatomicalMapDefinition = {
  id: "nasal-cavity",
  paired: true,
  svg: "/anatomy/nasal-cavity.svg",
  titleKey: "maps.nasalCavity",
  regions: [
    {
      id: "nose.vestibule",
      pathId: "nose-vestibule",
      labelKey: "nose.regions.vestibule",
      bodySiteCode: "ANAT.NASAL.VESTIBULE",
      ...nose,
    },
    {
      id: "nose.valve",
      pathId: "nose-valve",
      labelKey: "nose.regions.valve",
      bodySiteCode: "ANAT.NASAL.VALVE",
      ...nose,
    },
    {
      id: "nose.septum",
      pathId: "nose-septum",
      labelKey: "nose.regions.septum",
      bodySiteCode: "ANAT.NASAL.SEPTUM",
      ...nose,
    },
    {
      id: "nose.inferior-turbinate",
      pathId: "nose-it",
      labelKey: "nose.regions.inferiorTurbinate",
      bodySiteCode: "ANAT.NASAL.INFERIOR_TURBINATE",
      ...nose,
    },
    {
      id: "nose.middle-turbinate",
      pathId: "nose-mt",
      labelKey: "nose.regions.middleTurbinate",
      bodySiteCode: "ANAT.NASAL.MIDDLE_TURBINATE",
      ...nose,
    },
    {
      id: "nose.mucosa",
      pathId: "nose-mucosa",
      labelKey: "nose.regions.mucosa",
      bodySiteCode: "ANAT.NASAL.MUCOSA",
      ...nose,
    },
  ],
};
