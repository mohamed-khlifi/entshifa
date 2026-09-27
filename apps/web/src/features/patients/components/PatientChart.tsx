"use client";

import { AlertTriangle, Pill, ShieldAlert } from "lucide-react";
import { useState } from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { ConceptSearchField } from "../components/ConceptSearchField";
import {
  ChartBadge,
  PatientChartRow,
  type ChartBadgeTone,
} from "../components/PatientChartRow";
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
  useDeleteAllergyMutation,
  useDeleteHistoryMutation,
  useDeleteIdentifierMutation,
  useDeleteMedicationMutation,
  useDeleteProblemMutation,
  useEndFlagMutation,
} from "../hooks/use-patient-queries";
import { conceptDisplayText } from "../lib/concept-display";
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

const sectionClass =
  "space-y-4 rounded-2xl border border-border/80 bg-card p-5 shadow-[var(--shadow-soft)]";
const fieldClass = "space-y-1.5";
const listClass = "space-y-2";
const rowClass =
  "flex flex-wrap items-center justify-between gap-2 rounded-lg bg-muted/60 px-3 py-2.5 text-sm font-medium leading-snug";

function allergySeverityTone(
  severity: string | null | undefined,
): ChartBadgeTone {
  if (severity === "severe") {
    return "danger";
  }
  if (severity === "moderate") {
    return "warning";
  }
  return "neutral";
}

function problemStatusTone(status: string): ChartBadgeTone {
  if (status === "active") {
    return "success";
  }
  if (status === "suspected") {
    return "warning";
  }
  return "neutral";
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

  const requireConceptSelection = () => {
    toast.error(t("concept.selectRequired"));
  };
  const addIdentifier = useAddIdentifierMutation();
  const addAllergy = useAddAllergyMutation();
  const addMedication = useAddMedicationMutation();
  const addFlag = useAddFlagMutation();
  const addProblem = useAddProblemMutation();
  const addHistory = useAddHistoryMutation();
  const endFlag = useEndFlagMutation();
  const deleteIdentifier = useDeleteIdentifierMutation();
  const deleteAllergy = useDeleteAllergyMutation();
  const deleteMedication = useDeleteMedicationMutation();
  const deleteProblem = useDeleteProblemMutation();
  const deleteHistory = useDeleteHistoryMutation();

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
    <div className="space-y-5" {...testIdProps(testIds.patients.chart)}>
      <section className={sectionClass}>
        <h2 className="text-base font-semibold tracking-tight text-foreground">
          {t("chart.identifiers")}
        </h2>
        {patient.identifiers.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("chart.empty")}</p>
        ) : (
          <ul className={listClass}>
            {patient.identifiers.map((row) => (
              <PatientChartRow
                key={row.publicId}
                title={`${identifierTypeLabel(t, row.type)}: ${row.value}`}
                canWrite={canWrite}
                removeLabel={t("chart.remove")}
                removeTestId={testIds.patients.chartRemove(
                  "identifier",
                  row.publicId,
                )}
                onRemove={() => {
                  void deleteIdentifier
                    .mutateAsync({
                      patientId: patient.publicId,
                      itemId: row.publicId,
                    })
                    .catch(() => undefined);
                }}
              />
            ))}
          </ul>
        )}
        {canWrite ? (
          <form
            className="grid items-end gap-3 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              const country = issuingCountry.trim().toUpperCase();
              if (
                !identifierValue.trim() ||
                (country.length > 0 && country.length !== 2)
              ) {
                return;
              }
              void addIdentifier
                .mutateAsync({
                  patientId: patient.publicId,
                  body: {
                    type: identifierType,
                    value: identifierValue.trim(),
                    issuingCountry: country.length === 2 ? country : null,
                  },
                })
                .then(() => {
                  setIdentifierValue("");
                  setIssuingCountry("");
                })
                .catch(() => undefined);
            }}
          >
            <div className={fieldClass}>
              <Label>{t("chart.identifierType")}</Label>
              <Select
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
              </Select>
            </div>
            <div className={fieldClass}>
              <Label>{t("chart.identifierValue")}</Label>
              <Input
                value={identifierValue}
                onChange={(event) => setIdentifierValue(event.target.value)}
              />
            </div>
            <div className={fieldClass}>
              <Label>{t("chart.issuingCountry")}</Label>
              <Input
                value={issuingCountry}
                onChange={(event) => setIssuingCountry(event.target.value)}
                maxLength={2}
              />
              {issuingCountry.trim().length > 0 &&
              issuingCountry.trim().length !== 2 ? (
                <p className="text-sm text-destructive">
                  {t("validation.countryCode")}
                </p>
              ) : null}
            </div>
            <div className="flex items-end">
              <Button type="submit" size="lg">
                {t("chart.addIdentifier")}
              </Button>
            </div>
          </form>
        ) : null}
      </section>

      <section className={sectionClass}>
        <h2 className="text-base font-semibold tracking-tight text-foreground">
          {t("chart.allergies")}
        </h2>
        {patient.allergies.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("chart.empty")}</p>
        ) : (
          <ul className={listClass}>
            {patient.allergies.map((row) => (
              <PatientChartRow
                key={row.publicId}
                title={conceptDisplayText(row.substance)}
                badges={
                  <>
                    <ChartBadge tone="neutral">
                      {allergyCategoryLabel(t, row.category)}
                    </ChartBadge>
                    {row.severity ? (
                      <ChartBadge tone={allergySeverityTone(row.severity)}>
                        {row.severity === "severe" ? (
                          <AlertTriangle
                            className="h-3 w-3 shrink-0"
                            aria-hidden
                          />
                        ) : null}
                        {severityLabel(t, row.severity)}
                      </ChartBadge>
                    ) : null}
                    {!row.isActive ? (
                      <ChartBadge tone="neutral">
                        {t("chart.inactive")}
                      </ChartBadge>
                    ) : null}
                  </>
                }
                canWrite={canWrite}
                removeLabel={t("chart.remove")}
                removeTestId={testIds.patients.chartRemove(
                  "allergy",
                  row.publicId,
                )}
                onRemove={() => {
                  void deleteAllergy
                    .mutateAsync({
                      patientId: patient.publicId,
                      itemId: row.publicId,
                    })
                    .catch(() => undefined);
                }}
              />
            ))}
          </ul>
        )}
        {canWrite ? (
          <form
            className="grid items-start gap-3 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (substanceId.length !== 26) {
                requireConceptSelection();
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
                })
                .catch(() => undefined);
            }}
          >
            <ConceptSearchField
              className="sm:col-span-2"
              name="allergySubstance"
              label={t("chart.substance")}
              selectedId={substanceId}
              selectedDisplay={substanceDisplay}
              onSelect={(concept) => {
                setSubstanceId(concept.publicId);
                setSubstanceDisplay(concept.display);
              }}
              onClear={() => {
                setSubstanceId("");
                setSubstanceDisplay("");
              }}
            />
            <div className={fieldClass}>
              <Label>{t("chart.category")}</Label>
              <Select
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
              </Select>
            </div>
            <div className={fieldClass}>
              <Label>{t("chart.severity")}</Label>
              <Select
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
              </Select>
            </div>
            <div className="flex items-end">
              <Button type="submit" size="lg">
                {t("chart.addAllergy")}
              </Button>
            </div>
          </form>
        ) : null}
      </section>

      <section className={sectionClass}>
        <h2 className="text-base font-semibold tracking-tight text-foreground">
          {t("chart.medications")}
        </h2>
        {patient.medications.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("chart.empty")}</p>
        ) : (
          <ul className={listClass}>
            {patient.medications.map((row) => (
              <PatientChartRow
                key={row.publicId}
                title={row.freeTextName}
                badges={
                  <>
                    {row.isAnticoagulant ? (
                      <ChartBadge tone="danger">
                        <ShieldAlert className="h-3 w-3 shrink-0" aria-hidden />
                        {t("chart.anticoagulant")}
                      </ChartBadge>
                    ) : null}
                    {row.isOtotoxic ? (
                      <ChartBadge tone="warning">
                        <Pill className="h-3 w-3 shrink-0" aria-hidden />
                        {t("chart.ototoxic")}
                      </ChartBadge>
                    ) : null}
                    {!row.isActive ? (
                      <ChartBadge tone="neutral">
                        {t("chart.inactive")}
                      </ChartBadge>
                    ) : null}
                  </>
                }
                canWrite={canWrite}
                removeLabel={t("chart.remove")}
                removeTestId={testIds.patients.chartRemove(
                  "medication",
                  row.publicId,
                )}
                onRemove={() => {
                  void deleteMedication
                    .mutateAsync({
                      patientId: patient.publicId,
                      itemId: row.publicId,
                    })
                    .catch(() => undefined);
                }}
              />
            ))}
          </ul>
        )}
        {canWrite ? (
          <form
            className="grid items-end gap-3 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (!medName.trim()) {
                toast.error(t("validation.required"));
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
                })
                .catch(() => undefined);
            }}
          >
            <div className={fieldClass}>
              <Label>{t("chart.medicationName")}</Label>
              <Input
                value={medName}
                onChange={(event) => setMedName(event.target.value)}
              />
            </div>
            <div className={fieldClass}>
              <Label>{t("chart.dose")}</Label>
              <Input
                value={medDose}
                onChange={(event) => setMedDose(event.target.value)}
              />
            </div>
            <div className={fieldClass}>
              <Label>{t("chart.source")}</Label>
              <Select
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
              </Select>
            </div>
            <label className="flex h-11 items-center gap-2 rounded-lg border border-border bg-muted/40 px-3 text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 accent-primary"
                checked={isAnticoagulant}
                onChange={(event) => setIsAnticoagulant(event.target.checked)}
              />
              {t("chart.anticoagulant")}
            </label>
            <label className="flex h-11 items-center gap-2 rounded-lg border border-border bg-muted/40 px-3 text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 accent-primary"
                checked={isOtotoxic}
                onChange={(event) => setIsOtotoxic(event.target.checked)}
              />
              {t("chart.ototoxic")}
            </label>
            <div>
              <Button type="submit" size="lg">
                {t("chart.addMedication")}
              </Button>
            </div>
          </form>
        ) : null}
      </section>

      <section className={sectionClass}>
        <h2 className="text-base font-semibold tracking-tight">
          {t("chart.flags")}
        </h2>
        {patient.flags.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("chart.empty")}</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {patient.flags.map((row) => (
              <li key={row.publicId} className={rowClass}>
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
                      void endFlag
                        .mutateAsync({
                          patientId: patient.publicId,
                          flagId: row.publicId,
                          body: {
                            version: row.version,
                            endedOn: localIsoDate(),
                          },
                        })
                        .catch(() => undefined);
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
              void addFlag
                .mutateAsync({
                  patientId: patient.publicId,
                  body: {
                    flagCode,
                    startedOn: localIsoDate(),
                    isAuto: false,
                  },
                })
                .catch(() => undefined);
            }}
          >
            <div className={`${fieldClass} min-w-64 flex-1`}>
              <Label>{t("chart.flag")}</Label>
              <Select
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
              </Select>
            </div>
            <Button type="submit" size="lg">
              {t("chart.addFlag")}
            </Button>
          </form>
        ) : null}
      </section>

      <section className={sectionClass}>
        <h2 className="text-base font-semibold tracking-tight text-foreground">
          {t("chart.problems")}
        </h2>
        {patient.problems.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("chart.empty")}</p>
        ) : (
          <ul className={listClass}>
            {patient.problems.map((row) => (
              <PatientChartRow
                key={row.publicId}
                title={conceptDisplayText(row.diagnosis)}
                badges={
                  <>
                    <ChartBadge tone={problemStatusTone(row.status)}>
                      {problemStatusLabel(t, row.status)}
                    </ChartBadge>
                    <ChartBadge tone="neutral">
                      {lateralityLabel(tForms, t, row.laterality)}
                    </ChartBadge>
                  </>
                }
                canWrite={canWrite}
                removeLabel={t("chart.remove")}
                removeTestId={testIds.patients.chartRemove(
                  "problem",
                  row.publicId,
                )}
                onRemove={() => {
                  void deleteProblem
                    .mutateAsync({
                      patientId: patient.publicId,
                      itemId: row.publicId,
                    })
                    .catch(() => undefined);
                }}
              />
            ))}
          </ul>
        )}
        {canWrite ? (
          <form
            className="grid items-start gap-3 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (diagnosisId.length !== 26) {
                requireConceptSelection();
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
                })
                .catch(() => undefined);
            }}
          >
            <ConceptSearchField
              className="sm:col-span-2"
              name="problemDiagnosis"
              label={t("chart.diagnosis")}
              valueSetCode="tm.findings"
              selectedId={diagnosisId}
              selectedDisplay={diagnosisDisplay}
              onSelect={(concept) => {
                setDiagnosisId(concept.publicId);
                setDiagnosisDisplay(concept.display);
              }}
              onClear={() => {
                setDiagnosisId("");
                setDiagnosisDisplay("");
              }}
            />
            <div className={fieldClass}>
              <Label>{t("chart.status")}</Label>
              <Select
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
              </Select>
            </div>
            <div className={fieldClass}>
              <Label>{t("chart.laterality")}</Label>
              <Select
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
              </Select>
            </div>
            <div className="flex items-end">
              <Button type="submit" size="lg">
                {t("chart.addProblem")}
              </Button>
            </div>
          </form>
        ) : null}
      </section>

      <section className={sectionClass}>
        <h2 className="text-base font-semibold tracking-tight text-foreground">
          {t("chart.history")}
        </h2>
        {patient.history.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("chart.empty")}</p>
        ) : (
          <ul className={listClass}>
            {patient.history.map((row) => (
              <PatientChartRow
                key={row.publicId}
                title={
                  <>
                    <span className="text-muted-foreground">
                      {historyCategoryLabel(t, row.category)}:
                    </span>{" "}
                    {row.freeText || conceptDisplayText(row.concept)}
                  </>
                }
                canWrite={canWrite}
                removeLabel={t("chart.remove")}
                removeTestId={testIds.patients.chartRemove(
                  "history",
                  row.publicId,
                )}
                onRemove={() => {
                  void deleteHistory
                    .mutateAsync({
                      patientId: patient.publicId,
                      itemId: row.publicId,
                    })
                    .catch(() => undefined);
                }}
              />
            ))}
          </ul>
        )}
        {canWrite ? (
          <form
            className="grid items-end gap-3 sm:grid-cols-2"
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
                .then(() => setHistoryText(""))
                .catch(() => undefined);
            }}
          >
            <div className={fieldClass}>
              <Label>{t("chart.category")}</Label>
              <Select
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
              </Select>
            </div>
            <div className={fieldClass}>
              <Label>{t("chart.freeText")}</Label>
              <Input
                value={historyText}
                onChange={(event) => setHistoryText(event.target.value)}
              />
            </div>
            {historyError ? (
              <p className="text-sm text-destructive sm:col-span-2">
                {t("chart.historyNeedsText")}
              </p>
            ) : null}
            <div>
              <Button type="submit" size="lg">
                {t("chart.addHistory")}
              </Button>
            </div>
          </form>
        ) : null}
      </section>
    </div>
  );
}
