import { getTranslations } from "next-intl/server";
import type { ReactNode } from "react";

import { AuthBrandPanel } from "@/features/auth/components/AuthBrandPanel";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type AuthCardPageProps = {
  title: string;
  subtitle: string;
  testId: string;
  children: ReactNode;
};

export async function AuthCardPage({
  title,
  subtitle,
  testId,
  children,
}: AuthCardPageProps) {
  const tCommon = await getTranslations("common");

  return (
    <main className="grid min-h-screen lg:grid-cols-2" data-testid={testId}>
      <AuthBrandPanel />
      <section className="flex flex-col items-center justify-center px-6 py-12 sm:px-10">
        <div className="mb-8 flex items-center gap-3 lg:hidden">
          <span className="text-lg font-semibold tracking-tight text-foreground">
            {tCommon("app.name")}
          </span>
        </div>
        <Card className="w-full max-w-md border-border/80 shadow-md">
          <CardHeader>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{subtitle}</CardDescription>
          </CardHeader>
          <CardContent>{children}</CardContent>
        </Card>
      </section>
    </main>
  );
}
