import { getTranslations } from "next-intl/server";

import { ClinicAdminGate } from "@/features/clinics/components/ClinicAdminGate";
import { ClinicProfilePanel } from "@/features/clinics/components/ClinicProfilePanel";

export default async function AdminClinicPage() {
  const t = await getTranslations("clinics");

  return (
    <ClinicAdminGate>
      <div className="space-y-2 pb-6">
        <h1 className="text-2xl font-semibold tracking-tight">
          {t("profile.title")}
        </h1>
        <p className="text-sm text-muted-foreground">{t("profile.description")}</p>
      </div>
      <ClinicProfilePanel />
    </ClinicAdminGate>
  );
}
