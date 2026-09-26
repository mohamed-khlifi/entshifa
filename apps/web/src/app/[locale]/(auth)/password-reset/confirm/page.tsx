import { getTranslations } from "next-intl/server";

import { AuthCardPage, PasswordResetConfirmForm } from "@/features/auth";
import { testIds } from "@/lib/test/test-id";

type Props = {
  searchParams: Promise<{ token?: string }>;
};

export default async function PasswordResetConfirmPage({
  searchParams,
}: Props) {
  const t = await getTranslations("auth");
  const { token = "" } = await searchParams;

  return (
    <AuthCardPage
      title={t("passwordReset.confirmTitle")}
      subtitle={t("passwordReset.confirmSubtitle")}
      testId={testIds.auth.passwordReset.confirmRoot}
    >
      <PasswordResetConfirmForm token={token} />
    </AuthCardPage>
  );
}
