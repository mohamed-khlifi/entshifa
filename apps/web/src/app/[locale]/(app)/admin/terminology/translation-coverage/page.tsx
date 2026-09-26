import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { TerminologyAdminGate } from "@/features/terminology/components/TerminologyAdminGate";
import { TerminologyCoveragePanel } from "@/features/terminology/components/TerminologyCoveragePanel";

export default async function TerminologyCoveragePage() {
  const t = await getTranslations("terminology");
  return (
    <TerminologyAdminGate>
      <PageHeader
        title={t("coverage.title")}
        description={t("coverage.description")}
      />
      <TerminologyCoveragePanel />
    </TerminologyAdminGate>
  );
}
