import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { CalculatorWorkspace } from "@/features/calculators";

type PageProps = {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ patientId?: string; encounterId?: string }>;
};

export default async function CalculatorDetailPage({
  params,
  searchParams,
}: PageProps) {
  const t = await getTranslations("calculators");
  const { slug } = await params;
  const query = await searchParams;
  const code = decodeURIComponent(slug);

  return (
    <>
      <PageHeader title={t("page.title")} description={t("page.description")} />
      <CalculatorWorkspace
        slug={code}
        patientId={query.patientId}
        encounterId={query.encounterId}
      />
    </>
  );
}
