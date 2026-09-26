import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { UsersAdminGate } from "@/features/users/components/UsersAdminGate";
import { UsersAdminPanel } from "@/features/users/components/UsersAdminPanel";

export default async function AdminUsersPage() {
  const t = await getTranslations("users");

  return (
    <UsersAdminGate>
      <PageHeader
        title={t("list.title")}
        description={t("list.description")}
      />
      <UsersAdminPanel />
    </UsersAdminGate>
  );
}
