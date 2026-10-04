import { nasalCavityMap } from "@/lib/anatomy/nasal-cavity.map";
import { neckLevelsMap } from "@/lib/anatomy/neck-levels.map";
import { oralCavityMap } from "@/lib/anatomy/oral-cavity.map";
import { tympanicMembraneMap } from "@/lib/anatomy/tympanic-membrane.map";
import type { AnatomicalMapDefinition } from "@/lib/anatomy/types";

export const anatomicalMaps = [
  tympanicMembraneMap,
  nasalCavityMap,
  oralCavityMap,
  neckLevelsMap,
] as const;

const byId = new Map<string, AnatomicalMapDefinition>(
  anatomicalMaps.map((map) => [map.id, map]),
);

export function getAnatomicalMap(id: string): AnatomicalMapDefinition | null {
  return byId.get(id) ?? null;
}

export { nasalCavityMap, neckLevelsMap, oralCavityMap, tympanicMembraneMap };
