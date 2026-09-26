import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { TerminologyAdminGate } from "@/features/terminology/components/TerminologyAdminGate";
import { TerminologyConceptsPanel } from "@/features/terminology/components/TerminologyConceptsPanel";

export default async function TerminologyAdminPage() {
  const t = await getTranslations("terminology");
  return (
    <TerminologyAdminGate>
      <PageHeader title={t("concepts.title")} description={t("concepts.description")} />
      <TerminologyConceptsPanel />
    </TerminologyAdminGate>
  );
}
