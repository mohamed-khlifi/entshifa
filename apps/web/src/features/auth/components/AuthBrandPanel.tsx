import { Activity } from "lucide-react";
import { getTranslations } from "next-intl/server";

export async function AuthBrandPanel() {
  const t = await getTranslations("common");

  return (
    <aside
      className="relative hidden overflow-hidden lg:flex lg:flex-col lg:justify-between lg:p-12"
      style={{ background: "var(--gradient-brand)" }}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,hsl(0_0%_100%/0.12),transparent_50%)]" />
      <div className="relative flex items-center gap-3 text-primary-foreground">
        <span className="flex size-11 items-center justify-center rounded-xl bg-white/15 ring-1 ring-white/25 backdrop-blur-sm">
          <Activity className="size-6" strokeWidth={2.25} aria-hidden />
        </span>
        <span className="text-lg font-semibold tracking-tight">
          {t("app.name")}
        </span>
      </div>
      <div className="relative max-w-md space-y-4 text-primary-foreground">
        <p className="text-3xl font-semibold leading-tight tracking-tight">
          {t("app.tagline")}
        </p>
        <p className="text-sm leading-relaxed text-white/85">
          {t("app.clinicalNote")}
        </p>
      </div>
      <p className="relative text-xs text-white/70">
        {t("app.complianceHint")}
      </p>
    </aside>
  );
}
