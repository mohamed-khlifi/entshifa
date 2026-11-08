import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { CalculatorWorkspace } from "@/features/calculators";

type PageProps = {
  searchParams: Promise<{ patientId?: string; encounterId?: string }>;
};

export default async function CalculatorsIndexPage({
  searchParams,
}: PageProps) {
  const t = await getTranslations("calculators");
  const params = await searchParams;

  return (
    <>
      <PageHeader title={t("page.title")} description={t("page.description")} />
      <CalculatorWorkspace
        patientId={params.patientId}
        encounterId={params.encounterId}
      />
    </>
  );
}
