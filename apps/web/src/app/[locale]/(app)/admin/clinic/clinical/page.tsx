import { getTranslations } from "next-intl/server";

import { ClinicAdminGate, ClinicalSettingsPanel } from "@/features/clinics";
import { PageHeader } from "@/components/layout/PageHeader";

export default async function AdminClinicalSettingsPage() {
  const t = await getTranslations("clinics");

  return (
    <ClinicAdminGate>
      <PageHeader
        title={t("clinical.title")}
        description={t("clinical.description")}
      />
      <ClinicalSettingsPanel />
    </ClinicAdminGate>
  );
}
