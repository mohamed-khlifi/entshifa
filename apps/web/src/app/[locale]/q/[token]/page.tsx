import { setRequestLocale } from "next-intl/server";

import { PublicQuestionnaireRunner } from "@/features/questionnaires";

type PageProps = {
  params: Promise<{ locale: string; token: string }>;
};

export default async function PublicQuestionnairePage({ params }: PageProps) {
  const { locale, token } = await params;
  setRequestLocale(locale);
  return <PublicQuestionnaireRunner token={token} />;
}
