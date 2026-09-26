"use client";

import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { useRouter } from "@/lib/i18n/navigation";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

export function LogoutButton() {
  const t = useTranslations("common");
  const router = useRouter();
  const { logout } = useSession();

  const handleLogout = async () => {
    await logout();
    router.replace("/login");
  };

  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={() => void handleLogout()}
      {...testIdProps(testIds.layout.logout)}
    >
      {t("actions.logout")}
    </Button>
  );
}
