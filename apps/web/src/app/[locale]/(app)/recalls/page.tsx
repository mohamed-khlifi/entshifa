import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { RecallGate, RecallWorkList } from "@/features/recalls";

export default async function RecallsPage() {
  const t = await getTranslations("recalls");

  return (
    <RecallGate>
      <PageHeader title={t("page.title")} description={t("page.description")} />
      <RecallWorkList />
    </RecallGate>
  );
}
