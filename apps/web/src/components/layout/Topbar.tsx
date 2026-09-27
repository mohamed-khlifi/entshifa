"use client";

import { useTranslations } from "next-intl";

import { LogoutButton } from "@/features/auth";
import { ClinicSwitcher } from "@/components/layout/ClinicSwitcher";
import { LocaleSwitcher } from "@/components/layout/LocaleSwitcher";
import { testIdProps, testIds } from "@/lib/test/test-id";

export function Topbar() {
  const t = useTranslations("common");

  return (
    <header
      className="z-20 flex h-14 shrink-0 items-center justify-between gap-4 border-b border-border bg-card/95 px-4 shadow-sm backdrop-blur-md"
      {...testIdProps(testIds.layout.topbar)}
    >
      <span className="bg-gradient-to-r from-primary to-[hsl(199_70%_36%)] bg-clip-text text-sm font-semibold tracking-tight text-transparent">
        {t("app.name")}
      </span>
      <div className="flex items-center gap-2 sm:gap-3">
        <ClinicSwitcher />
        <LocaleSwitcher />
        <LogoutButton />
      </div>
    </header>
  );
}
