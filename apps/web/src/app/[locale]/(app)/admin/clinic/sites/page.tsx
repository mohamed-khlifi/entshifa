import { getTranslations } from "next-intl/server";

import { ClinicAdminGate, SitesPanel } from "@/features/clinics";
import { PageHeader } from "@/components/layout/PageHeader";
import { Link } from "@/lib/i18n/navigation";

export default async function AdminClinicSitesPage() {
  const t = await getTranslations("clinics");

  return (
    <ClinicAdminGate>
      <PageHeader
        title={t("sites.title")}
        description={t("sites.description")}
        actions={
          <Link
            href="/admin/clinic/clinical"
            className="text-sm font-medium text-primary hover:underline"
          >
            {t("nav.clinical")}
          </Link>
        }
      />
      <SitesPanel />
    </ClinicAdminGate>
  );
}
