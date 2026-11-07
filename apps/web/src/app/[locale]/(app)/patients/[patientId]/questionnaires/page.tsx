import { getTranslations, setRequestLocale } from "next-intl/server";

import { QuestionnaireDeliveryPanel } from "@/features/questionnaires";
import { testIdProps, testIds } from "@/lib/test/test-id";

type PageProps = {
  params: Promise<{ locale: string; patientId: string }>;
};

export default async function PatientQuestionnairesPage({ params }: PageProps) {
  const { locale, patientId } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("questionnaires");
  return (
    <div
      className="space-y-4"
      {...testIdProps(testIds.questionnaires.patientPage)}
    >
      <h1 className="text-xl font-semibold">{t("delivery.title")}</h1>
      <QuestionnaireDeliveryPanel patientId={patientId} />
    </div>
  );
}
