import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { MfaSecurityPanel } from "@/features/settings/components/MfaSecurityPanel";

export default async function SecuritySettingsPage() {
  const t = await getTranslations("settings");

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("security.title")}
        description={t("security.description")}
      />
      <MfaSecurityPanel />
    </div>
  );
}
