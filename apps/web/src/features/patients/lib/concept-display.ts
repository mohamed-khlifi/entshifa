/** Locale-resolved concept label from API payloads (never show raw codes alone). */

export type ConceptLike = {
  display?: string | null;
  code?: string | null;
  conceptId: string;
};

export function conceptDisplayText(concept: ConceptLike | null | undefined): string {
  if (!concept) {
    return "";
  }
  const display = concept.display?.trim();
  if (display) {
    return display;
  }
  const code = concept.code?.trim();
  if (code) {
    return code.replaceAll(".", " · ");
  }
  return concept.conceptId;
}
