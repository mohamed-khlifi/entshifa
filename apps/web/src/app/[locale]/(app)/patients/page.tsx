import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { PatientsGate, PatientsListPanel } from "@/features/patients";

export default async function PatientsPage() {
  const t = await getTranslations("patients");

  return (
    <PatientsGate>
      <PageHeader title={t("list.title")} description={t("list.description")} />
      <PatientsListPanel />
    </PatientsGate>
  );
}
