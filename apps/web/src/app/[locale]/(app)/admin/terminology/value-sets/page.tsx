import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { TerminologyAdminGate } from "@/features/terminology/components/TerminologyAdminGate";
import { TerminologyValueSetsPanel } from "@/features/terminology/components/TerminologyValueSetsPanel";

export default async function TerminologyValueSetsPage() {
  const t = await getTranslations("terminology");
  return (
    <TerminologyAdminGate>
      <PageHeader
        title={t("valueSets.title")}
        description={t("valueSets.description")}
      />
      <TerminologyValueSetsPanel />
    </TerminologyAdminGate>
  );
}
