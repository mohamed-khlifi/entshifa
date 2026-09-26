import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/layout/PageHeader";
import { PatientCreateForm, PatientsGate } from "@/features/patients";

export default async function NewPatientPage() {
  const t = await getTranslations("patients");

  return (
    <PatientsGate>
      <PageHeader
        title={t("form.createTitle")}
        description={t("form.createDescription")}
      />
      <PatientCreateForm />
    </PatientsGate>
  );
}
