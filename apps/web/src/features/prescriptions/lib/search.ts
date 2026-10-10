import type {
  DrugRead,
  FormularyEntryRead,
  PrescriptionTemplateRead,
} from "@/lib/api/generated";

export function templatesForVisit(
  templates: readonly PrescriptionTemplateRead[],
  complaintConceptIds: readonly string[],
  query: string,
): PrescriptionTemplateRead[] {
  const needle = query.trim().toLowerCase();
  const complaints = new Set(complaintConceptIds);
  const specific = templates.filter((template) =>
    template.complaintConceptIds.some((id) => complaints.has(id)),
  );
  const general =
    specific.length > 0
      ? []
      : templates.filter(
          (template) => template.complaintConceptIds.length === 0,
        );
  const ranked = [...specific, ...general];
  if (needle.length === 0) {
    return ranked;
  }
  return ranked.filter(
    (template) =>
      template.code.toLowerCase().includes(needle) ||
      template.nameKey.toLowerCase().includes(needle),
  );
}

export function catalogOnlyDrugs(
  drugs: readonly DrugRead[],
  formulary: readonly FormularyEntryRead[],
): DrugRead[] {
  const onFormulary = new Set(formulary.map((entry) => entry.drug.publicId));
  return drugs.filter((drug) => !onFormulary.has(drug.publicId));
}

export function templateTitle(
  template: PrescriptionTemplateRead,
  translated: string | null,
): string {
  if (translated && translated.trim().length > 0) {
    return translated;
  }
  return template.code.replaceAll("_", " ");
}
