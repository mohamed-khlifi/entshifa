"use client";

import { useLocale, useTranslations } from "next-intl";

import {
  conceptDisplayText,
  PatientSafetyAlertBanner,
} from "@/features/patients";
import type { EncounterRead, PatientRead } from "@/lib/api/generated";
import {
  formatDate,
  formatPersonName,
  patientAgeDisplay,
} from "@/lib/i18n/format";
import { Link } from "@/lib/i18n/navigation";
import { encounterVisitTestId, testIdProps, testIds } from "@/lib/test/test-id";

type CockpitPatientColumnProps = {
  patient: PatientRead;
  visits: readonly EncounterRead[];
};

export function CockpitPatientColumn({
  patient,
  visits,
}: CockpitPatientColumnProps) {
  const t = useTranslations("encounters");
  const locale = useLocale();
  const age = patientAgeDisplay(patient.birthDate);
  const ageText =
    age === null
      ? null
      : age.unit === "years"
        ? t("patientCard.ageYears", { count: age.count })
        : t("patientCard.ageMonths", { count: age.count });
  const allergies = patient.allergies.filter((row) => row.isActive);
  const problems = patient.problems.filter((row) => row.status === "active");
  const medications = patient.medications.filter((row) => row.isActive);

  return (
    <aside
      className="space-y-4"
      {...testIdProps(testIds.encounters.patientCard)}
    >
      <PatientSafetyAlertBanner flags={patient.flags} />
      <div className="space-y-1">
        <h2 className="text-xl font-semibold">
          {formatPersonName(
            { given: patient.firstName, family: patient.lastName },
            locale,
          )}
        </h2>
        {ageText ? <p className="text-sm text-primary">{ageText}</p> : null}
        <p className="text-xs text-muted-foreground">
          {t("patientCard.mrn", { mrn: patient.mrn })}
        </p>
      </div>
      <FactList
        title={t("patientCard.allergies")}
        empty={t("patientCard.none")}
        items={allergies.map((row) => conceptDisplayText(row.substance))}
      />
      <FactList
        title={t("patientCard.problems")}
        empty={t("patientCard.none")}
        items={problems.map((row) => conceptDisplayText(row.diagnosis))}
      />
      <FactList
        title={t("patientCard.medications")}
        empty={t("patientCard.none")}
        items={medications.flatMap((row) =>
          row.freeTextName ? [row.freeTextName] : [],
        )}
      />
      <section
        className="space-y-1"
        {...testIdProps(testIds.encounters.visits)}
      >
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {t("patientCard.visits")}
        </h3>
        {visits.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("patientCard.visitsEmpty")}
          </p>
        ) : (
          <ul className="space-y-1">
            {visits.map((visit) => (
              <li key={visit.publicId}>
                <Link
                  href={`/patients/${patient.publicId}/encounters/${visit.publicId}`}
                  className="text-sm text-primary underline-offset-2 hover:underline"
                  {...testIdProps(encounterVisitTestId(visit.publicId))}
                >
                  <span>{formatDate(visit.startedAt, locale)}</span>
                  {visit.chiefComplaintSummary ? (
                    <span className="ms-2">{visit.chiefComplaintSummary}</span>
                  ) : null}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section {...testIdProps(testIds.encounters.questionnaire)}>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {t("patientCard.questionnaire")}
        </h3>
        <p className="text-sm text-muted-foreground">
          {t("patientCard.questionnaireEmpty")}
        </p>
      </section>
    </aside>
  );
}

function FactList({
  title,
  empty,
  items,
}: {
  title: string;
  empty: string;
  items: string[];
}) {
  return (
    <section className="space-y-1">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h3>
      {items.length === 0 ? (
        <p className="text-sm">{empty}</p>
      ) : (
        <ul className="space-y-0.5 text-sm">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
