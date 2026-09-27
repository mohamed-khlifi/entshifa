export type ConceptOption = {
  publicId: string;
  display: string;
};

export function filterConceptOptions(
  options: ConceptOption[],
  query: string,
): ConceptOption[] {
  const term = query.trim().toLowerCase();
  if (!term) {
    return options;
  }
  return options.filter((item) => item.display.toLowerCase().includes(term));
}

export function conceptOptionsFromDictionary(
  concepts: Record<string, { publicId: string; display: string }>,
): ConceptOption[] {
  return Object.values(concepts)
    .map((item) => ({
      publicId: item.publicId,
      display: item.display,
    }))
    .sort((left, right) => left.display.localeCompare(right.display));
}
