import { getTranslations } from "next-intl/server";

import { AuthCardPage } from "@/features/auth/components/AuthCardPage";
import { InviteAcceptForm } from "@/features/auth/components/InviteAcceptForm";
import { testIds } from "@/lib/test/test-id";

type Props = {
  searchParams: Promise<{ token?: string }>;
};

export default async function InviteAcceptPage({ searchParams }: Props) {
  const t = await getTranslations("auth");
  const { token = "" } = await searchParams;

  return (
    <AuthCardPage
      title={t("invite.title")}
      subtitle={t("invite.subtitle")}
      testId={testIds.auth.invite.root}
    >
      <InviteAcceptForm token={token} />
    </AuthCardPage>
  );
}
