import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { UsersAdminGate, UsersAdminPanel } from "@/features/users";

export default async function AdminUsersPage() {
  const t = await getTranslations("users");

  return (
    <UsersAdminGate>
      <PageHeader title={t("list.title")} description={t("list.description")} />
      <UsersAdminPanel />
    </UsersAdminGate>
  );
}
