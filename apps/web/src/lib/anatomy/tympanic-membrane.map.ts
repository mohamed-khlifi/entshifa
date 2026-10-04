import type { AnatomicalMapDefinition } from "@/lib/anatomy/types";

const membrane = {
  valueSetCode: "tm.findings",
  defaultNormalCode: "FIND.TM.NORMAL",
} as const;

export const tympanicMembraneMap: AnatomicalMapDefinition = {
  id: "tympanic-membrane",
  paired: true,
  svg: "/anatomy/tympanic-membrane.svg",
  titleKey: "maps.tympanicMembrane",
  regions: [
    {
      id: "tm.canal",
      pathId: "tm-canal",
      labelKey: "tm.regions.canal",
      bodySiteCode: "ANAT.EAR.CANAL",
      valueSetCode: "tm.canal.findings",
      defaultNormalCode: "FIND.CANAL.NORMAL",
    },
    {
      id: "tm.pars-flaccida",
      pathId: "tm-pf",
      labelKey: "tm.regions.parsFlaccida",
      bodySiteCode: "ANAT.TM.PF",
      ...membrane,
    },
    {
      id: "tm.pars-tensa.antero-superior",
      pathId: "tm-pt-as",
      labelKey: "tm.regions.anteroSuperior",
      bodySiteCode: "ANAT.TM.PT.AS",
      ...membrane,
    },
    {
      id: "tm.pars-tensa.antero-inferior",
      pathId: "tm-pt-ai",
      labelKey: "tm.regions.anteroInferior",
      bodySiteCode: "ANAT.TM.PT.AI",
      ...membrane,
    },
    {
      id: "tm.pars-tensa.postero-inferior",
      pathId: "tm-pt-pi",
      labelKey: "tm.regions.posteroInferior",
      bodySiteCode: "ANAT.TM.PT.PI",
      ...membrane,
    },
    {
      id: "tm.pars-tensa.postero-superior",
      pathId: "tm-pt-ps",
      labelKey: "tm.regions.posteroSuperior",
      bodySiteCode: "ANAT.TM.PT.PS",
      ...membrane,
    },
  ],
};
