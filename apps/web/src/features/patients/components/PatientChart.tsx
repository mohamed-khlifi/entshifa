"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ConceptSearchField } from "../components/ConceptSearchField";
import {
  ALLERGY_CATEGORIES,
  ALLERGY_SEVERITIES,
  HISTORY_CATEGORIES,
  IDENTIFIER_TYPES,
  MEDICATION_SOURCES,
  PATIENT_FLAG_CODES,
  PROBLEM_STATUSES,
} from "../constants";
import {
  useAddAllergyMutation,
  useAddFlagMutation,
  useAddHistoryMutation,
  useAddIdentifierMutation,
  useAddMedicationMutation,
  useAddProblemMutation,
  useEndFlagMutation,
} from "../hooks/use-patient-queries";
import { isFlagActive, localIsoDate } from "../lib/active-flags";
import {
  allergyCategoryLabel,
  flagLabel,
  historyCategoryLabel,
  identifierTypeLabel,
  medicationSourceLabel,
  problemStatusLabel,
  severityLabel,
} from "../lib/labels";
import type { PatientRead } from "@/lib/api/generated";
import { Permission } from "@/lib/permissions";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { usePermission } from "@/providers/permission-provider";

const selectClass =
  "flex h-10 w-full rounded-lg border border-input bg-card px-3 text-sm";

function conceptText(
  concept: {
    display?: string | null;
    code?: string | null;
    conceptId: string;
  } | null,
): string {
  if (!concept) {
    return "";
  }
  return concept.display || concept.code || concept.conceptId;
}

function lateralityLabel(
  tForms: ReturnType<typeof useTranslations<"forms">>,
  t: ReturnType<typeof useTranslations<"patients">>,
  value: string,
): string {
  switch (value) {
    case "left":
      return tForms("laterality.left");
    case "right":
      return tForms("laterality.right");
    case "bilateral":
      return tForms("laterality.bilateral");
    case "midline":
      return t("laterality.midline");
    default:
      return t("laterality.na");
  }
}

const LATERALITY = ["right", "left", "bilateral", "midline", "na"] as const;

export function PatientChart({ patient }: { patient: PatientRead }) {
  const t = useTranslations("patients");
  const tForms = useTranslations("forms");
  const canWrite = usePermission(Permission.PATIENT_WRITE);
  const addIdentifier = useAddIdentifierMutation();
  const addAllergy = useAddAllergyMutation();
  const addMedication = useAddMedicationMutation();
  const addFlag = useAddFlagMutation();
  const addProblem = useAddProblemMutation();
  const addHistory = useAddHistoryMutation();
  const endFlag = useEndFlagMutation();

  const [identifierType, setIdentifierType] =
    useState<(typeof IDENTIFIER_TYPES)[number]>("national_id");
  const [identifierValue, setIdentifierValue] = useState("");
  const [issuingCountry, setIssuingCountry] = useState("");
  const [substanceId, setSubstanceId] = useState("");
  const [substanceDisplay, setSubstanceDisplay] = useState("");
  const [category, setCategory] =
    useState<(typeof ALLERGY_CATEGORIES)[number]>("drug");
  const [severity, setSeverity] = useState<
    "" | (typeof ALLERGY_SEVERITIES)[number]
  >("");
  const [medName, setMedName] = useState("");
  const [medDose, setMedDose] = useState("");
  const [medSource, setMedSource] =
    useState<(typeof MEDICATION_SOURCES)[number]>("reported");
  const [isAnticoagulant, setIsAnticoagulant] = useState(false);
  const [isOtotoxic, setIsOtotoxic] = useState(false);
  const [flagCode, setFlagCode] =
    useState<(typeof PATIENT_FLAG_CODES)[number]>("only_hearing_ear");
  const [diagnosisId, setDiagnosisId] = useState("");
  const [diagnosisDisplay, setDiagnosisDisplay] = useState("");
  const [problemStatus, setProblemStatus] =
    useState<(typeof PROBLEM_STATUSES)[number]>("active");
  const [laterality, setLaterality] =
    useState<(typeof LATERALITY)[number]>("na");
  const [historyCategory, setHistoryCategory] =
    useState<(typeof HISTORY_CATEGORIES)[number]>("ent_surgery");
  const [historyText, setHistoryText] = useState("");
  const [historyError, setHistoryError] = useState(false);

  return (
    <div className="space-y-8" {...testIdProps(testIds.patients.chart)}>
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">{t("chart.identifiers")}</h2>
        {patient.identifiers.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("chart.empty")}</p>
        ) : (
          <ul className="space-y-1 text-sm">
            {patient.identifiers.map((row) => (
              <li key={row.publicId}>
                {identifierTypeLabel(t, row.type)}: {row.value}
              </li>
            ))}
          </ul>
        )}
        {canWrite ? (
          <form
            className="grid gap-3 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (!identifierValue.trim()) {
                return;
              }
              void addIdentifier
                .mutateAsync({
                  patientId: patient.publicId,
                  body: {
                    type: identifierType,
                    value: identifierValue.trim(),
                    issuingCountry: issuingCountry.trim()
                      ? issuingCountry.trim().toUpperCase()
                      : null,
                  },
                })
                .then(() => {
                  setIdentifierValue("");
                  setIssuingCountry("");
                });
            }}
          >
            <label className="space-y-1 text-sm">
              <Label>{t("chart.identifierType")}</Label>
              <select
                className={selectClass}
                value={identifierType}
                onChange={(event) =>
                  setIdentifierType(event.target.value as typeof identifierType)
                }
              >
                {IDENTIFIER_TYPES.map((value) => (
                  <option key={value} value={value}>
                    {identifierTypeLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              <Label>{t("chart.identifierValue")}</Label>
              <Input
                value={identifierValue}
                onChange={(event) => setIdentifierValue(event.target.value)}
              />
            </label>
            <label className="space-y-1 text-sm">
              <Label>{t("chart.issuingCountry")}</Label>
              <Input
                value={issuingCountry}
                onChange={(event) => setIssuingCountry(event.target.value)}
                maxLength={2}
              />
            </label>
            <div className="flex items-end">
              <Button type="submit">{t("chart.addIdentifier")}</Button>
            </div>
          </form>
        ) : null}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">{t("chart.allergies")}</h2>
        {patient.allergies.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("chart.empty")}</p>
        ) : (
          <ul className="space-y-1 text-sm">
            {patient.allergies.map((row) => (
              <li key={row.publicId}>
                {conceptText(row.substance)} (
                {allergyCategoryLabel(t, row.category)}
                {row.severity ? `, ${severityLabel(t, row.severity)}` : ""})
                {row.isActive ? "" : ` — ${t("chart.inactive")}`}
              </li>
            ))}
          </ul>
        )}
        {canWrite ? (
          <form
            className="grid gap-3 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (substanceId.length !== 26) {
                return;
              }
              void addAllergy
                .mutateAsync({
                  patientId: patient.publicId,
                  body: {
                    substanceConceptId: substanceId,
                    category,
                    severity: severity || null,
                    isActive: true,
                  },
                })
                .then(() => {
                  setSubstanceId("");
                  setSubstanceDisplay("");
                  setSeverity("");
                });
            }}
          >
            <ConceptSearchField
              name="allergySubstance"
              label={t("chart.substance")}
              selectedId={substanceId}
              selectedDisplay={substanceDisplay}
              onSelect={(concept) => {
                setSubstanceId(concept.publicId);
                setSubstanceDisplay(concept.display);
              }}
            />
            <label className="space-y-1 text-sm">
              <Label>{t("chart.category")}</Label>
              <select
                className={selectClass}
                value={category}
                onChange={(event) =>
                  setCategory(event.target.value as typeof category)
                }
              >
                {ALLERGY_CATEGORIES.map((value) => (
                  <option key={value} value={value}>
                    {allergyCategoryLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              <Label>{t("chart.severity")}</Label>
              <select
                className={selectClass}
                value={severity}
                onChange={(event) =>
                  setSeverity(event.target.value as typeof severity)
                }
              >
                <option value="">{t("list.filters.any")}</option>
                {ALLERGY_SEVERITIES.map((value) => (
                  <option key={value} value={value}>
                    {severityLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex items-end">
              <Button type="submit">{t("chart.addAllergy")}</Button>
            </div>
          </form>
        ) : null}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">{t("chart.medications")}</h2>
        {patient.medications.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("chart.empty")}</p>
        ) : (
          <ul className="space-y-1 text-sm">
            {patient.medications.map((row) => (
              <li key={row.publicId}>
                {row.freeTextName}
                {row.isAnticoagulant ? ` (${t("chart.anticoagulant")})` : ""}
                {row.isOtotoxic ? ` (${t("chart.ototoxic")})` : ""}
                {row.isActive ? "" : ` — ${t("chart.inactive")}`}
              </li>
            ))}
          </ul>
        )}
        {canWrite ? (
          <form
            className="grid gap-3 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (!medName.trim()) {
                return;
              }
              void addMedication
                .mutateAsync({
                  patientId: patient.publicId,
                  body: {
                    freeTextName: medName.trim(),
                    dose: medDose.trim() || null,
                    source: medSource,
                    isActive: true,
                    isAnticoagulant,
                    isOtotoxic,
                  },
                })
                .then(() => {
                  setMedName("");
                  setMedDose("");
                  setIsAnticoagulant(false);
                  setIsOtotoxic(false);
                });
            }}
          >
            <label className="space-y-1 text-sm">
              <Label>{t("chart.medicationName")}</Label>
              <Input
                value={medName}
                onChange={(event) => setMedName(event.target.value)}
              />
            </label>
            <label className="space-y-1 text-sm">
              <Label>{t("chart.dose")}</Label>
              <Input
                value={medDose}
                onChange={(event) => setMedDose(event.target.value)}
              />
            </label>
            <label className="space-y-1 text-sm">
              <Label>{t("chart.source")}</Label>
              <select
                className={selectClass}
                value={medSource}
                onChange={(event) =>
                  setMedSource(event.target.value as typeof medSource)
                }
              >
                {MEDICATION_SOURCES.map((value) => (
                  <option key={value} value={value}>
                    {medicationSourceLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={isAnticoagulant}
                onChange={(event) => setIsAnticoagulant(event.target.checked)}
              />
              {t("chart.anticoagulant")}
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={isOtotoxic}
                onChange={(event) => setIsOtotoxic(event.target.checked)}
              />
              {t("chart.ototoxic")}
            </label>
            <div>
              <Button type="submit">{t("chart.addMedication")}</Button>
            </div>
          </form>
        ) : null}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">{t("chart.flags")}</h2>
        {patient.flags.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("chart.empty")}</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {patient.flags.map((row) => (
              <li
                key={row.publicId}
                className="flex flex-wrap items-center gap-2"
              >
                <span>
                  {flagLabel(t, row.flagCode)}
                  {isFlagActive(row)
                    ? ` (${t("chart.active")})`
                    : ` (${t("chart.inactive")})`}
                </span>
                {canWrite && isFlagActive(row) ? (
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    onClick={() => {
                      void endFlag.mutateAsync({
                        patientId: patient.publicId,
                        flagId: row.publicId,
                        body: { version: row.version, endedOn: localIsoDate() },
                      });
                    }}
                  >
                    {t("chart.endFlag")}
                  </Button>
                ) : null}
              </li>
            ))}
          </ul>
        )}
        {canWrite ? (
          <form
            className="flex flex-wrap items-end gap-3"
            onSubmit={(event) => {
              event.preventDefault();
              void addFlag.mutateAsync({
                patientId: patient.publicId,
                body: {
                  flagCode,
                  startedOn: localIsoDate(),
                  isAuto: false,
                },
              });
            }}
          >
            <label className="space-y-1 text-sm">
              <Label>{t("chart.flag")}</Label>
              <select
                className={selectClass}
                value={flagCode}
                onChange={(event) =>
                  setFlagCode(event.target.value as typeof flagCode)
                }
              >
                {PATIENT_FLAG_CODES.map((code) => (
                  <option key={code} value={code}>
                    {flagLabel(t, code)}
                  </option>
                ))}
              </select>
            </label>
            <Button type="submit">{t("chart.addFlag")}</Button>
          </form>
        ) : null}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">{t("chart.problems")}</h2>
        {patient.problems.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("chart.empty")}</p>
        ) : (
          <ul className="space-y-1 text-sm">
            {patient.problems.map((row) => (
              <li key={row.publicId}>
                {conceptText(row.diagnosis)} (
                {problemStatusLabel(t, row.status)},{" "}
                {lateralityLabel(tForms, t, row.laterality)})
              </li>
            ))}
          </ul>
        )}
        {canWrite ? (
          <form
            className="grid gap-3 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (diagnosisId.length !== 26) {
                return;
              }
              void addProblem
                .mutateAsync({
                  patientId: patient.publicId,
                  body: {
                    diagnosisConceptId: diagnosisId,
                    laterality,
                    status: problemStatus,
                  },
                })
                .then(() => {
                  setDiagnosisId("");
                  setDiagnosisDisplay("");
                });
            }}
          >
            <ConceptSearchField
              name="problemDiagnosis"
              label={t("chart.diagnosis")}
              selectedId={diagnosisId}
              selectedDisplay={diagnosisDisplay}
              onSelect={(concept) => {
                setDiagnosisId(concept.publicId);
                setDiagnosisDisplay(concept.display);
              }}
            />
            <label className="space-y-1 text-sm">
              <Label>{t("chart.status")}</Label>
              <select
                className={selectClass}
                value={problemStatus}
                onChange={(event) =>
                  setProblemStatus(event.target.value as typeof problemStatus)
                }
              >
                {PROBLEM_STATUSES.map((value) => (
                  <option key={value} value={value}>
                    {problemStatusLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              <Label>{t("chart.laterality")}</Label>
              <select
                className={selectClass}
                value={laterality}
                onChange={(event) =>
                  setLaterality(event.target.value as typeof laterality)
                }
              >
                {LATERALITY.map((value) => (
                  <option key={value} value={value}>
                    {lateralityLabel(tForms, t, value)}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex items-end">
              <Button type="submit">{t("chart.addProblem")}</Button>
            </div>
          </form>
        ) : null}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">{t("chart.history")}</h2>
        {patient.history.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("chart.empty")}</p>
        ) : (
          <ul className="space-y-1 text-sm">
            {patient.history.map((row) => (
              <li key={row.publicId}>
                {historyCategoryLabel(t, row.category)}:{" "}
                {row.freeText || conceptText(row.concept)}
              </li>
            ))}
          </ul>
        )}
        {canWrite ? (
          <form
            className="grid gap-3 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (!historyText.trim()) {
                setHistoryError(true);
                return;
              }
              setHistoryError(false);
              void addHistory
                .mutateAsync({
                  patientId: patient.publicId,
                  body: {
                    category: historyCategory,
                    freeText: historyText.trim(),
                  },
                })
                .then(() => setHistoryText(""));
            }}
          >
            <label className="space-y-1 text-sm">
              <Label>{t("chart.category")}</Label>
              <select
                className={selectClass}
                value={historyCategory}
                onChange={(event) =>
                  setHistoryCategory(
                    event.target.value as typeof historyCategory,
                  )
                }
              >
                {HISTORY_CATEGORIES.map((value) => (
                  <option key={value} value={value}>
                    {historyCategoryLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              <Label>{t("chart.freeText")}</Label>
              <Input
                value={historyText}
                onChange={(event) => setHistoryText(event.target.value)}
              />
            </label>
            {historyError ? (
              <p className="text-sm text-destructive sm:col-span-2">
                {t("chart.historyNeedsText")}
              </p>
            ) : null}
            <div>
              <Button type="submit">{t("chart.addHistory")}</Button>
            </div>
          </form>
        ) : null}
      </section>
    </div>
  );
}
