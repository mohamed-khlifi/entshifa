import { getTranslations } from "next-intl/server";

import { AuthCardPage, PasswordResetRequestForm } from "@/features/auth";
import { testIds } from "@/lib/test/test-id";

export default async function PasswordResetPage() {
  const t = await getTranslations("auth");

  return (
    <AuthCardPage
      title={t("passwordReset.title")}
      subtitle={t("passwordReset.subtitle")}
      testId={testIds.auth.passwordReset.root}
    >
      <PasswordResetRequestForm />
    </AuthCardPage>
  );
}
