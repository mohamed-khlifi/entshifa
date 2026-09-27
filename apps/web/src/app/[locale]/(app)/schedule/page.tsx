import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { ScheduleGate, SchedulePanel } from "@/features/scheduling";

export default async function SchedulePage() {
  const t = await getTranslations("scheduling");

  return (
    <ScheduleGate>
      <PageHeader title={t("page.title")} description={t("page.description")} />
      <SchedulePanel />
    </ScheduleGate>
  );
}
