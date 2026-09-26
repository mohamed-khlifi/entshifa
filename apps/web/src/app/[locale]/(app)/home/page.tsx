import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { testIdProps, testIds } from "@/lib/test/test-id";

export default async function HomePage() {
  const t = await getTranslations("common");

  return (
    <div className="space-y-6">
      <PageHeader title={t("nav.home")} />
      <section className="rounded-xl border border-border/80 bg-card p-6 text-card-foreground shadow-[var(--shadow-soft)]">
        <h2
          className="text-lg font-medium"
          {...testIdProps(testIds.layout.homeTitle)}
        >
          {t("home.welcome")}
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {t("home.signedInAs")}
        </p>
      </section>
    </div>
  );
}
