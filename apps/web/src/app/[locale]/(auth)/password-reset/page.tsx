import { getTranslations } from "next-intl/server";

import { AuthCardPage } from "@/features/auth/components/AuthCardPage";
import { PasswordResetRequestForm } from "@/features/auth/components/PasswordResetRequestForm";
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
