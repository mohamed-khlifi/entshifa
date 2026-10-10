"use client";

import { NextIntlClientProvider, useTranslations } from "next-intl";

import { testIdProps, testIds } from "@/lib/test/test-id";
import ar from "../../../../../../packages/i18n-messages/ar/prescriptions.json";
import en from "../../../../../../packages/i18n-messages/en/prescriptions.json";
import fr from "../../../../../../packages/i18n-messages/fr/prescriptions.json";

import type { PaperLocale } from "../constants";
import { routeLabel } from "../lib/labels";
import type { PaperModel } from "../lib/paper";

const CATALOGS = { en, fr, ar } as const;

type PrescriptionPaperProps = {
  locale: PaperLocale;
  model: PaperModel;
};

export function PrescriptionPaper({ locale, model }: PrescriptionPaperProps) {
  return (
    <NextIntlClientProvider
      locale={locale}
      messages={{ prescriptions: CATALOGS[locale] }}
    >
      <PaperBody model={model} />
    </NextIntlClientProvider>
  );
}

function PaperBody({ model }: { model: PaperModel }) {
  const t = useTranslations("prescriptions");
  return (
    <article
      className="hidden space-y-4 bg-card p-6 text-sm print:block"
      {...testIdProps(testIds.prescriptions.paper)}
    >
      <header className="space-y-1 border-b border-border pb-3">
        <h1 className="text-xl font-semibold">
          {model.legalName || model.clinicName}
        </h1>
        {model.addressLines.map((line) => (
          <p key={line}>{line}</p>
        ))}
        {model.phone ? <p>{model.phone}</p> : null}
        {model.email ? <p>{model.email}</p> : null}
        {model.registrationNumber ? (
          <p>{t("print.registration", { value: model.registrationNumber })}</p>
        ) : null}
        {model.taxId ? <p>{t("print.tax", { value: model.taxId })}</p> : null}
      </header>
      <h2 className="text-lg font-semibold">{t("print.title")}</h2>
      <p>
        {t("print.patient")}: {model.patientName}
      </p>
      <p>{t("print.born", { date: model.birthDate })}</p>
      <p>{t("print.mrn", { mrn: model.mrn })}</p>
      {model.weightKg ? (
        <p>{t("print.weight", { weight: model.weightKg })}</p>
      ) : null}
      {model.identifier ? (
        <p>{t("print.identifier", { id: model.identifier })}</p>
      ) : null}
      <ol className="list-decimal space-y-3 ps-5">
        {model.lines.map((line, index) => (
          <li key={`${line.title}-${index}`}>
            <p className="font-medium">{line.title}</p>
            {line.dose && line.unit ? (
              <p>
                {t("print.line", {
                  dose: line.dose,
                  unit: line.unit,
                  route: routeLabel(t, line.route),
                  frequency: line.frequencyPerDay,
                  duration: line.durationDays,
                })}
              </p>
            ) : null}
            {line.instructions ? <p>{line.instructions}</p> : null}
            {line.renewable ? <p>{t("print.renewable")}</p> : null}
            <p>
              {line.substitutionAllowed
                ? t("print.substitutionAllowed")
                : t("print.noSubstitution")}
            </p>
            {line.taper.length > 0 ? (
              <ul>
                {line.taper.map((day) => (
                  <li key={day.day}>
                    {t("helpers.taperDay", { day: day.day, dose: day.doseMg })}
                  </li>
                ))}
              </ul>
            ) : null}
          </li>
        ))}
      </ol>
      <p className="pt-8">{t("print.signature")}</p>
    </article>
  );
}
