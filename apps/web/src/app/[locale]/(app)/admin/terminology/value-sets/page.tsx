import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import {
  TerminologyAdminGate,
  TerminologyValueSetsPanel,
} from "@/features/terminology";

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
