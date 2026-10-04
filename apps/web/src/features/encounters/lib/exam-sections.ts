const SECTION_TO_MAP: Record<string, string> = {
  ear: "tympanic-membrane",
  neck: "neck-levels",
  nose: "nasal-cavity",
  oral_cavity: "oral-cavity",
};

export function mapsForSections(sections: readonly string[]): string[] {
  const ids: string[] = [];
  for (const section of sections) {
    const mapId = SECTION_TO_MAP[section];
    if (mapId && !ids.includes(mapId)) {
      ids.push(mapId);
    }
  }
  return ids;
}

export function unmappedSections(sections: readonly string[]): string[] {
  return sections.filter((section) => !(section in SECTION_TO_MAP));
}
