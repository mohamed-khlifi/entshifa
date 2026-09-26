import { getTranslations } from "next-intl/server";

import { ClinicAdminGate } from "@/features/clinics/components/ClinicAdminGate";
import { ClinicalSettingsPanel } from "@/features/clinics/components/ClinicalSettingsPanel";
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
