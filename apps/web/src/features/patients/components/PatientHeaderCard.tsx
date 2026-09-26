"use client";

import { useLocale, useTranslations } from "next-intl";

import type { PatientRead } from "@/lib/api/generated";
import { formatPersonName, patientAgeDisplay } from "@/lib/i18n/format";
import { testIdProps, testIds } from "@/lib/test/test-id";

function conceptText(concept: {
  display?: string | null;
  code?: string | null;
  conceptId: string;
}): string {
  return concept.display || concept.code || concept.conceptId;
}

type PatientHeaderCardProps = {
  patient: PatientRead;
};

export function PatientHeaderCard({ patient }: PatientHeaderCardProps) {
  const t = useTranslations("patients");
  const locale = useLocale();
  const age = patientAgeDisplay(patient.birthDate);
  const ageText =
    age === null
      ? null
      : age.unit === "years"
        ? t("header.ageYears", { count: age.count })
        : t("header.ageMonths", { count: age.count });
  const allergies = patient.allergies.filter((row) => row.isActive);
  const problems = patient.problems.filter((row) => row.status === "active");
  const medications = patient.medications.filter((row) => row.isActive);

  return (
    <section
      className="rounded-xl border border-border bg-card p-5 shadow-[var(--shadow-soft)]"
      {...testIdProps(testIds.patients.header)}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">
            {formatPersonName(
              { given: patient.firstName, family: patient.lastName },
              locale,
            )}
          </h2>
          <p className="text-sm text-muted-foreground">
            {t("header.mrn", { mrn: patient.mrn })}
          </p>
        </div>
        <div className="text-sm">
          {ageText ? (
            <p {...testIdProps(testIds.patients.headerAge)}>{ageText}</p>
          ) : null}
          {patient.birthDateIsEstimated ? (
            <p className="text-muted-foreground">{t("header.estimated")}</p>
          ) : null}
          {patient.isDeceased ? (
            <p className="font-medium text-destructive">
              {t("header.deceased")}
            </p>
          ) : null}
        </div>
      </div>
      <dl className="mt-4 grid gap-4 sm:grid-cols-2">
        <div {...testIdProps(testIds.patients.headerAllergies)}>
          <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t("header.allergies")}
          </dt>
          <dd className="mt-1 text-sm">
            {allergies.length === 0
              ? t("header.none")
              : allergies.map((row) => conceptText(row.substance)).join(", ")}
          </dd>
        </div>
        <div {...testIdProps(testIds.patients.headerProblems)}>
          <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t("header.problems")}
          </dt>
          <dd className="mt-1 text-sm">
            {problems.length === 0
              ? t("header.none")
              : problems.map((row) => conceptText(row.diagnosis)).join(", ")}
          </dd>
        </div>
        <div {...testIdProps(testIds.patients.headerMedications)}>
          <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t("header.medications")}
          </dt>
          <dd className="mt-1 text-sm">
            {medications.length === 0
              ? t("header.none")
              : medications
                  .map((row) => row.freeTextName)
                  .filter(Boolean)
                  .join(", ")}
          </dd>
        </div>
        <div {...testIdProps(testIds.patients.headerVisits)}>
          <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t("header.lastVisits")}
          </dt>
          <dd className="mt-1 text-sm text-muted-foreground">
            {t("header.lastVisitsEmpty")}
          </dd>
        </div>
      </dl>
    </section>
  );
}
