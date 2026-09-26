import { getTranslations } from "next-intl/server";

import { AuthBrandPanel, LoginForm } from "@/features/auth";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { testIdProps, testIds } from "@/lib/test/test-id";

export default async function LoginPage() {
  const t = await getTranslations("auth");
  const tCommon = await getTranslations("common");

  return (
    <main
      className="grid min-h-screen lg:grid-cols-2"
      {...testIdProps(testIds.auth.login.root)}
    >
      <AuthBrandPanel />
      <section className="flex flex-col items-center justify-center px-6 py-12 sm:px-10">
        <div className="mb-8 flex items-center gap-3 lg:hidden">
          <span className="text-lg font-semibold tracking-tight text-foreground">
            {tCommon("app.name")}
          </span>
        </div>
        <Card className="w-full max-w-md border-border/80">
          <CardHeader>
            <CardTitle>{t("login.title")}</CardTitle>
            <CardDescription>{t("login.subtitle")}</CardDescription>
          </CardHeader>
          <CardContent>
            <LoginForm />
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
