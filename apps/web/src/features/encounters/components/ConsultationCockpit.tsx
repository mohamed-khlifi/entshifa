"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { AutosaveIndicator } from "@/components/forms/AutosaveIndicator";
import { Form } from "@/components/forms/Form";
import { TextAreaField } from "@/components/forms/TextAreaField";
import { Button } from "@/components/ui/button";
import { NormalsToolbar, selectCopySource } from "@/features/examination";
import {
  anatomicalMaps,
  nasalCavityMap,
  neckLevelsMap,
  oralCavityMap,
  tympanicMembraneMap,
} from "@/lib/anatomy";
import {
  examinationStateFromCopy,
  markAllNormal,
  markSectionNormal,
  toAllObservationCreates,
  toFullNarrativeDrafts,
} from "@/lib/anatomy/examination-state";
import type {
  AnatomicalMapDefinition,
  MapSide,
  MapState,
} from "@/lib/anatomy/types";
import type { EncounterRead, NarrativeFindingIn } from "@/lib/api/generated";
import { queryKeys } from "@/lib/api/query-keys";
import { clearDraftSnapshot, readDraftSnapshot } from "@/lib/forms/autosave";
import { Permission } from "@/lib/permissions";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { Can, usePermission } from "@/providers/permission-provider";

import {
  addEncounterAddendum,
  addProblem,
  recordVisitObservations,
  searchDiagnoses,
  signEncounter,
} from "../api/encounters.api";
import {
  chiefComplaintSummary,
  composeClinicalNote,
  type NoteLine,
} from "../lib/clinical-note";
import {
  makePrimary,
  primaryComplaint,
  toggleComplaint,
  type ComplaintChoice,
  type SelectedComplaint,
} from "../lib/complaints";
import type { DiagnosisDraft } from "../lib/cockpit-state";
import { problemStatusFor } from "../lib/cockpit-state";
import type { EncounterFieldSnapshot } from "../lib/encounter-patch";
import { mapsForSections, unmappedSections } from "../lib/exam-sections";
import { draftKey, resolveHydration } from "../lib/hydration";
import type { CockpitDraftEnvelope } from "../lib/hydration";
import {
  courseLabel,
  diagnosisSideLabel,
  diagnosisStatusLabel,
  historyLateralityLabel,
  planKindLabel,
  redFlagLabel,
} from "../lib/labels";
import {
  removePlanItem,
  toggleSuggestion,
  type PlanItemDraft,
} from "../lib/plan-items";
import { toggleRedFlag, type RedFlagId } from "../lib/red-flags";
import { parseTemplateConfig } from "../lib/template-config";
import {
  templateFieldLabel,
  templateOptionLabel,
} from "../lib/template-labels";
import {
  cockpitDefaultValues,
  cockpitFormSchema,
  type CockpitFormValues,
} from "../schemas/cockpit.schema";
import { AssessmentPanel } from "./AssessmentPanel";
import { ComplaintSelector } from "./ComplaintSelector";
import { CockpitPatientColumn } from "./CockpitPatientColumn";
import { ExamSection } from "./ExamSection";
import { HistorySection } from "./HistorySection";
import { PlanPanel } from "./PlanPanel";
import { RedFlagList } from "./RedFlagList";
import { ReportPreview } from "./ReportPreview";
import { SuggestionPanel } from "./SuggestionPanel";
import {
  useConsultationSession,
  useCopyVisit,
  useTemplateRoute,
  useVisitNarrative,
} from "../hooks/use-consultation-session";
import { useEncounterAutosave } from "../hooks/use-encounter-autosave";

type ConsultationCockpitProps = {
  patientId: string;
  encounterId?: string;
};

type EditorState = {
  complaints: SelectedComplaint[];
  redFlags: RedFlagId[];
  diagnoses: DiagnosisDraft[];
  planItems: PlanItemDraft[];
  examByMap: Record<string, MapState>;
  expandedMaps: string[];
};

const emptyEditor: EditorState = {
  complaints: [],
  redFlags: [],
  diagnoses: [],
  planItems: [],
  examByMap: {},
  expandedMaps: [],
};

export function ConsultationCockpit({
  patientId,
  encounterId,
}: ConsultationCockpitProps) {
  const t = useTranslations("encounters");
  const tExam = useTranslations("examination");
  const session = useConsultationSession(patientId, encounterId);
  const [override, setOverride] = useState<EncounterRead | null>(null);
  const encounter =
    override &&
    (override.publicId === encounterId ||
      override.publicId === session.active?.publicId)
      ? override
      : session.active;
  const [editor, setEditor] = useState<EditorState>(emptyEditor);
  const [ready, setReady] = useState(false);
  const [resetToken, setResetToken] = useState(0);
  const [version, setVersion] = useState(1);
  const [signOpen, setSignOpen] = useState(false);
  const hydratedKey = useRef<string | null>(null);
  const form = useForm<CockpitFormValues>({
    resolver: zodResolver(cockpitFormSchema),
    defaultValues: cockpitDefaultValues,
  });
  const values = form.watch();
  const locked = encounter?.status !== "draft";
  const canSign = usePermission(Permission.ENCOUNTER_SIGN);

  useEffect(() => {
    if (!encounter) {
      return;
    }
    const key = `${encounter.publicId}:${resetToken}`;
    if (hydratedKey.current === key) {
      return;
    }
    hydratedKey.current = key;
    let cancelled = false;
    void (async () => {
      const stored = await readDraftSnapshot<
        CockpitDraftEnvelope<EditorState & { form: CockpitFormValues }>
      >(draftKey(encounter.publicId));
      if (cancelled) {
        return;
      }
      const decision = resolveHydration(stored, encounter.version);
      if (decision.source === "draft" && decision.state) {
        setEditor({
          complaints: decision.state.complaints,
          redFlags: decision.state.redFlags,
          diagnoses: decision.state.diagnoses,
          planItems: decision.state.planItems,
          examByMap: decision.state.examByMap,
          expandedMaps: decision.state.expandedMaps,
        });
        form.reset(decision.state.form);
      } else {
        setEditor({
          ...emptyEditor,
          complaints: complaintsFromEncounter(encounter),
        });
        form.reset({
          ...cockpitDefaultValues,
          historyNote: encounter.historyText ?? "",
          assessmentNote: encounter.assessmentText ?? "",
          planNote: encounter.planText ?? "",
        });
      }
      setVersion(encounter.version);
      setReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [encounter, form, resetToken]);

  const codes = editor.complaints.map((item) => item.code);
  const primary = primaryComplaint(editor.complaints);
  const templateQuery = useTemplateRoute(codes, primary?.code ?? null);
  const templateConfig = parseTemplateConfig(templateQuery.data?.config);
  const templateCode = templateQuery.data?.code ?? "";
  const appliedTemplate = useRef("");

  useEffect(() => {
    if (!templateCode || appliedTemplate.current === templateCode) {
      return;
    }
    appliedTemplate.current = templateCode;
    setEditor((current) => ({
      ...current,
      expandedMaps: mapsForSections(templateConfig.examSections),
    }));
  }, [templateCode, templateConfig.examSections]);

  const historyText = composeClinicalNote(
    historyLines(values, templateConfig.historyFields, t),
    values.historyNote,
    (line) => t("note.line", line),
  );
  const assessmentText = composeClinicalNote(
    editor.diagnoses.map((row) => ({
      label: row.display,
      value: t("assessment.line", {
        display: row.display,
        laterality: diagnosisSideLabel(t, row.laterality),
        status: diagnosisStatusLabel(t, row.status),
      }),
    })),
    values.assessmentNote,
    (line) => line.value,
  );
  const planText = composeClinicalNote(
    editor.planItems.map((item) => ({
      label: planKindLabel(t, item.kind),
      value: t("plan.line", {
        kind: planKindLabel(t, item.kind),
        detail: item.detail,
      }),
    })),
    values.planNote,
    (line) => line.value,
  );
  const currentSnapshot = useMemo<EncounterFieldSnapshot>(
    () => ({
      chiefComplaintSummary: chiefComplaintSummary(primary?.display ?? null),
      historyText,
      assessmentText,
      planText,
      complaints: editor.complaints.map((item, index) => ({
        conceptCode: item.code,
        isPrimary: item.isPrimary,
        laterality: null,
        durationText: null,
        sortOrder: index,
      })),
    }),
    [
      assessmentText,
      editor.complaints,
      historyText,
      planText,
      primary?.display,
    ],
  );
  const serverSnapshot = useMemo(
    () => (encounter ? snapshotFromEncounter(encounter) : null),
    [encounter],
  );
  const draft = useMemo(() => {
    if (!encounter || !ready) {
      return null;
    }
    return {
      baseVersion: version,
      state: { ...editor, form: values },
    };
  }, [editor, encounter, ready, values, version]);
  const autosave = useEncounterAutosave({
    encounterId: encounter?.publicId ?? null,
    version,
    enabled: ready && !locked && Boolean(session.scope.enabled),
    scope: session.scope,
    serverSnapshot,
    currentSnapshot,
    draft,
    resetToken,
    onVersion: setVersion,
  });
  const findings = toFullNarrativeDrafts(anatomicalMaps, editor.examByMap);
  const narrative = useVisitNarrative(
    patientId,
    findings as NarrativeFindingIn[],
  );
  const copyVisit = useCopyVisit(patientId);
  const queryClient = useQueryClient();
  const copySource = selectCopySource(
    session.encounters.data?.items ?? [],
    encounter?.publicId ?? null,
  );

  if (session.loading && !encounter) {
    return (
      <p {...testIdProps(testIds.encounters.loading)}>{t("layout.loading")}</p>
    );
  }
  if (session.failed && !encounter) {
    return (
      <p {...testIdProps(testIds.encounters.error)}>{t("layout.error")}</p>
    );
  }
  if (session.needsSite) {
    return (
      <p {...testIdProps(testIds.encounters.needsSite)}>
        {t("layout.needsSite")}
      </p>
    );
  }
  if (!encounter || !session.patient.data) {
    return (
      <p {...testIdProps(testIds.encounters.loading)}>{t("layout.loading")}</p>
    );
  }

  const selectedSources = new Set(
    editor.planItems.flatMap((item) => (item.source ? [item.source] : [])),
  );

  function applySection(definition: AnatomicalMapDefinition, side?: MapSide) {
    setEditor((current) => {
      const previous = current.examByMap[definition.id] ?? {
        side: side ?? "right",
        marks: {},
      };
      return {
        ...current,
        examByMap: {
          ...current.examByMap,
          [definition.id]: {
            side: side ?? previous.side,
            marks: {
              ...previous.marks,
              ...markSectionNormal(definition, side),
            },
          },
        },
        expandedMaps: current.expandedMaps.includes(definition.id)
          ? current.expandedMaps
          : [...current.expandedMaps, definition.id],
      };
    });
  }

  async function handleCopy() {
    if (!copySource) {
      return;
    }
    const result = await copyVisit.mutateAsync({
      sourceEncounterId: copySource.publicId,
      body: {
        startedAt: new Date().toISOString(),
        sitePublicId: copySource.sitePublicId,
      },
    });
    hydratedKey.current = `${result.encounter.publicId}:${resetToken}`;
    setOverride(result.encounter);
    setVersion(result.encounter.version);
    setEditor({
      ...emptyEditor,
      complaints: complaintsFromEncounter(result.encounter),
      examByMap: examinationStateFromCopy(
        anatomicalMaps,
        result.observations.items,
        result.snapshots.items,
        copySource.publicId,
      ),
    });
    form.reset({
      ...cockpitDefaultValues,
      historyNote: result.encounter.historyText ?? "",
      assessmentNote: result.encounter.assessmentText ?? "",
      planNote: result.encounter.planText ?? "",
    });
    setReady(true);
    toast.success(t("toast.copy"));
  }

  async function handleSign() {
    if (!encounter) {
      return;
    }
    await autosave.flush();
    const observations = toAllObservationCreates(
      anatomicalMaps,
      editor.examByMap,
      new Date().toISOString(),
    );
    if (observations.length > 0) {
      await recordVisitObservations(
        patientId,
        {
          encounterPublicId: encounter.publicId,
          observations,
        },
        session.scope,
      );
    }
    const signed = await signEncounter(
      encounter.publicId,
      { role: "clinician" },
      session.scope,
    );
    await clearDraftSnapshot(draftKey(encounter.publicId));
    setOverride(signed);
    setSignOpen(false);
    toast.success(t("toast.signed"));
    await queryClient.invalidateQueries({
      queryKey: queryKeys.encounters.patient(patientId),
    });
  }

  async function promote(row: DiagnosisDraft) {
    await addProblem(
      patientId,
      {
        diagnosisConceptId: row.conceptPublicId,
        laterality: row.laterality,
        status: problemStatusFor(row.status),
      },
      session.scope,
      crypto.randomUUID(),
    );
    setEditor((current) => ({
      ...current,
      diagnoses: current.diagnoses.map((item) =>
        item.conceptPublicId === row.conceptPublicId
          ? { ...item, promoted: true }
          : item,
      ),
    }));
    await queryClient.invalidateQueries({
      queryKey: queryKeys.patients.detail(patientId),
    });
  }

  return (
    <div className="pb-36" {...testIdProps(testIds.encounters.root)}>
      <div className="grid items-start gap-4 lg:grid-cols-12">
        <div className="lg:sticky lg:top-0 lg:col-span-3 lg:max-h-[calc(100svh-15rem)] lg:self-start lg:overflow-y-auto print:hidden">
          <CockpitPatientColumn
            patient={session.patient.data}
            visits={session.recentVisits}
          />
        </div>
        <div className="space-y-6 lg:col-span-6 print:hidden">
          {locked ? (
            <p
              className="rounded-lg border border-border bg-muted px-3 py-2 text-sm"
              {...testIdProps(testIds.encounters.signed)}
            >
              {t("status.signed")}
            </p>
          ) : null}
          {autosave.conflict ? (
            <div
              className="space-y-2 rounded-lg border border-destructive p-3"
              {...testIdProps(testIds.encounters.conflict)}
            >
              <h2 className="font-semibold">{t("conflict.title")}</h2>
              <p className="text-sm">
                {t("conflict.body", {
                  serverVersion: autosave.conflict.serverVersion,
                  clientVersion: autosave.conflict.clientVersion,
                })}
              </p>
              <Button
                type="button"
                onClick={() => {
                  hydratedKey.current = null;
                  setReady(false);
                  setResetToken((value) => value + 1);
                  void queryClient.invalidateQueries({
                    queryKey: queryKeys.encounters.patient(patientId),
                  });
                }}
                {...testIdProps(testIds.encounters.conflictReload)}
              >
                {t("conflict.reload")}
              </Button>
            </div>
          ) : null}
          <Form form={form} onSubmit={() => undefined}>
            <ComplaintSelector
              members={(session.complaints.data?.members ?? []).map(
                (member) => ({
                  code: member.code,
                  conceptPublicId: member.publicId,
                  display: member.display,
                }),
              )}
              selected={editor.complaints}
              disabled={locked}
              onToggle={(choice: ComplaintChoice) =>
                setEditor((current) => ({
                  ...current,
                  complaints: toggleComplaint(current.complaints, choice),
                }))
              }
              onMakePrimary={(code) =>
                setEditor((current) => ({
                  ...current,
                  complaints: makePrimary(current.complaints, code),
                }))
              }
            />
            <HistorySection
              fields={templateConfig.historyFields}
              disabled={locked}
            />
            <RedFlagList
              complaintCodes={codes}
              confirmed={editor.redFlags}
              disabled={locked}
              onToggle={(flag) =>
                setEditor((current) => ({
                  ...current,
                  redFlags: toggleRedFlag(current.redFlags, flag),
                }))
              }
            />
            <SuggestionPanel
              tests={templateConfig.suggestedTests}
              instruments={templateConfig.suggestedInstruments}
              documents={templateConfig.suggestedDocuments}
              pendingSections={unmappedSections(templateConfig.examSections)}
              selectedSources={selectedSources}
              disabled={locked}
              followUpDays={templateConfig.defaultFollowUpDays}
              onToggle={(source, kind, detail) =>
                setEditor((current) => ({
                  ...current,
                  planItems: toggleSuggestion(
                    current.planItems,
                    source,
                    kind,
                    detail,
                    crypto.randomUUID(),
                  ),
                }))
              }
              onFollowUp={() => {
                if (templateConfig.defaultFollowUpDays === null) {
                  return;
                }
                setEditor((current) => ({
                  ...current,
                  planItems: toggleSuggestion(
                    current.planItems,
                    "follow-up",
                    "follow_up",
                    t("plan.followUpDetail", {
                      days: templateConfig.defaultFollowUpDays ?? 0,
                    }),
                    crypto.randomUUID(),
                  ),
                }));
              }}
            />
            <ExamSection
              byMap={editor.examByMap}
              expanded={editor.expandedMaps}
              disabled={locked}
              onChange={(examByMap) =>
                setEditor((current) => ({ ...current, examByMap }))
              }
              onToggle={(mapId) =>
                setEditor((current) => ({
                  ...current,
                  expandedMaps: current.expandedMaps.includes(mapId)
                    ? current.expandedMaps.filter((id) => id !== mapId)
                    : [...current.expandedMaps, mapId],
                }))
              }
            />
            <AssessmentPanel
              rows={editor.diagnoses}
              favorites={templateConfig.favoriteDiagnoses}
              disabled={locked}
              onAdd={(row) =>
                setEditor((current) => ({
                  ...current,
                  diagnoses: current.diagnoses.some(
                    (item) => item.conceptPublicId === row.conceptPublicId,
                  )
                    ? current.diagnoses
                    : [...current.diagnoses, row],
                }))
              }
              onChange={(conceptPublicId, patch) =>
                setEditor((current) => ({
                  ...current,
                  diagnoses: current.diagnoses.map((row) =>
                    row.conceptPublicId === conceptPublicId
                      ? { ...row, ...patch }
                      : row,
                  ),
                }))
              }
              onRemove={(conceptPublicId) =>
                setEditor((current) => ({
                  ...current,
                  diagnoses: current.diagnoses.filter(
                    (row) => row.conceptPublicId !== conceptPublicId,
                  ),
                }))
              }
              onPromote={(row) => {
                void promote(row);
              }}
              onFavorite={(code) => {
                void searchDiagnoses(code, session.scope).then((result) => {
                  const match =
                    result.items.find((item) => item.code === code) ??
                    result.items[0];
                  if (!match) {
                    toast.error(t("assessment.favoriteMissing"));
                    return;
                  }
                  setEditor((current) => ({
                    ...current,
                    diagnoses: current.diagnoses.some(
                      (item) => item.conceptPublicId === match.publicId,
                    )
                      ? current.diagnoses
                      : [
                          ...current.diagnoses,
                          {
                            conceptPublicId: match.publicId,
                            display: match.display,
                            laterality: "na",
                            status: "suspected",
                            promoted: false,
                          },
                        ],
                  }));
                });
              }}
            />
            <PlanPanel
              items={editor.planItems}
              disabled={locked}
              onAdd={(kind, detail) =>
                setEditor((current) => ({
                  ...current,
                  planItems: [
                    ...current.planItems,
                    { id: crypto.randomUUID(), kind, detail },
                  ],
                }))
              }
              onRemove={(id) =>
                setEditor((current) => ({
                  ...current,
                  planItems: removePlanItem(current.planItems, id),
                }))
              }
            />
          </Form>
          {locked ? (
            <Can permission={Permission.ENCOUNTER_AMEND}>
              <AddendumForm
                onSubmit={async (body) => {
                  const updated = await addEncounterAddendum(
                    encounter.publicId,
                    { body },
                    session.scope,
                  );
                  setOverride(updated);
                  toast.success(t("addendum.saved"));
                }}
              />
            </Can>
          ) : null}
        </div>
        <div className="lg:sticky lg:top-0 lg:col-span-3 lg:max-h-[calc(100svh-15rem)] lg:self-start lg:overflow-y-auto">
          <ReportPreview
            complaints={editor.complaints
              .map((item) => item.display)
              .join("\n")}
            history={historyText}
            examination={narrative.data?.text ?? ""}
            flags={editor.redFlags
              .map((flag) => redFlagLabel(t, flag))
              .join("\n")}
            assessment={assessmentText}
            plan={planText}
          />
        </div>
      </div>
      <div
        className="fixed bottom-0 end-0 start-0 z-20 border-t border-border bg-card/95 backdrop-blur md:start-56 print:hidden"
        {...testIdProps(testIds.encounters.bottomBar)}
      >
        <div className="space-y-2 px-3 py-2">
          <div className="flex items-center gap-2">
            <div className="me-auto">
              <AutosaveIndicator status={autosave.status} />
            </div>
            <Button
              type="button"
              variant="secondary"
              onClick={() => window.print()}
              {...testIdProps(testIds.encounters.print)}
            >
              {t("actions.print")}
            </Button>
            {canSign && !locked ? (
              <Button
                type="button"
                onClick={() => setSignOpen(true)}
                {...testIdProps(testIds.encounters.sign)}
              >
                {t("actions.sign")}
              </Button>
            ) : null}
          </div>
          <NormalsToolbar
            compact
            canCopy={copySource !== null && !locked}
            copying={copyVisit.isPending}
            onNormalAll={() =>
              setEditor((current) => ({
                ...current,
                examByMap: markAllNormal(anatomicalMaps),
                expandedMaps: anatomicalMaps.map((map) => map.id),
              }))
            }
            onOtoscopyRight={() => applySection(tympanicMembraneMap, "right")}
            onOtoscopyLeft={() => applySection(tympanicMembraneMap, "left")}
            onRhinoscopy={() => applySection(nasalCavityMap)}
            onOral={() => applySection(oralCavityMap)}
            onNeck={() => applySection(neckLevelsMap)}
            onCopy={() => {
              void handleCopy();
            }}
            labels={{
              group: tExam("normals.group"),
              all: tExam("normals.all"),
              otoscopyRight: tExam("normals.otoscopyRight"),
              otoscopyLeft: tExam("normals.otoscopyLeft"),
              rhinoscopy: tExam("normals.rhinoscopy"),
              oral: tExam("normals.oral"),
              neck: tExam("normals.neck"),
              copy: tExam("copyForward.action"),
              unavailable: tExam("copyForward.unavailable"),
            }}
          />
        </div>
      </div>
      <SignDialog
        open={signOpen}
        title={t("sign.title")}
        body={t("sign.body")}
        cancelLabel={t("sign.cancel")}
        confirmLabel={t("sign.confirm")}
        onCancel={() => setSignOpen(false)}
        onConfirm={() => {
          void handleSign();
        }}
      />
    </div>
  );
}

function historyLines(
  values: CockpitFormValues,
  fields: ReturnType<typeof parseTemplateConfig>["historyFields"],
  t: ReturnType<typeof useTranslations<"encounters">>,
): NoteLine[] {
  const lines: NoteLine[] = [];
  push(lines, t("history.onset"), values.onset);
  push(lines, t("history.course"), courseLabel(t, values.course));
  push(
    lines,
    t("history.laterality"),
    historyLateralityLabel(t, values.laterality),
  );
  if (values.severity !== null) {
    push(lines, t("history.severity"), String(values.severity));
  }
  push(lines, t("history.triggers"), values.triggers);
  push(lines, t("history.relievingFactors"), values.relievingFactors);
  push(lines, t("history.previousTreatments"), values.previousTreatments);
  push(lines, t("history.previousConsultations"), values.previousConsultations);
  push(lines, t("history.impact"), values.impact);
  for (const field of fields) {
    const raw = values.templateAnswers[field.id];
    const label = templateFieldLabel(t, field.labelKey);
    if (field.fieldType === "boolean" && typeof raw === "boolean") {
      push(lines, label, raw ? t("history.yes") : t("history.no"));
    } else if (field.fieldType === "number" && typeof raw === "number") {
      push(lines, label, String(raw));
    } else if (typeof raw === "string" && raw.trim().length > 0) {
      push(
        lines,
        label,
        field.fieldType === "select"
          ? templateOptionLabel(t, field.id, raw)
          : raw,
      );
    } else if (Array.isArray(raw)) {
      for (const option of raw) {
        push(lines, label, templateOptionLabel(t, field.id, option));
      }
    }
  }
  return lines;
}

function push(lines: NoteLine[], label: string, value: string) {
  if (value.trim().length > 0) {
    lines.push({ label, value });
  }
}

function complaintsFromEncounter(
  encounter: EncounterRead,
): SelectedComplaint[] {
  return encounter.complaints.flatMap((row) => {
    const code = row.concept.code;
    if (!code) {
      return [];
    }
    return [
      {
        code,
        conceptPublicId: row.concept.conceptId,
        display: row.concept.display || code,
        isPrimary: row.isPrimary,
      },
    ];
  });
}

function snapshotFromEncounter(
  encounter: EncounterRead,
): EncounterFieldSnapshot {
  return {
    chiefComplaintSummary: encounter.chiefComplaintSummary ?? null,
    historyText: encounter.historyText ?? null,
    assessmentText: encounter.assessmentText ?? null,
    planText: encounter.planText ?? null,
    complaints: encounter.complaints.flatMap((row, index) => {
      const code = row.concept.code;
      if (!code) {
        return [];
      }
      return [
        {
          conceptCode: code,
          isPrimary: row.isPrimary,
          laterality: row.laterality ?? null,
          durationText: row.durationText ?? null,
          sortOrder: row.sortOrder ?? index,
        },
      ];
    }),
  };
}

function SignDialog({
  open,
  title,
  body,
  cancelLabel,
  confirmLabel,
  onCancel,
  onConfirm,
}: {
  open: boolean;
  title: string;
  body: string;
  cancelLabel: string;
  confirmLabel: string;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const node = dialogRef.current;
    if (!node) {
      return;
    }
    if (open && !node.open) {
      if (typeof node.showModal === "function") {
        node.showModal();
      } else {
        node.setAttribute("open", "");
      }
    }
    if (!open && node.open) {
      if (typeof node.close === "function") {
        node.close();
      } else {
        node.removeAttribute("open");
      }
    }
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      className="w-full max-w-md space-y-3 rounded-xl border-0 bg-card p-5 shadow-[var(--shadow-soft)] backdrop:bg-foreground/40"
      onCancel={(event) => {
        event.preventDefault();
        onCancel();
      }}
      {...testIdProps(testIds.encounters.signDialog)}
    >
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="text-sm">{body}</p>
      <div className="flex justify-end gap-2">
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          {...testIdProps(testIds.encounters.signCancel)}
        >
          {cancelLabel}
        </Button>
        <Button
          type="button"
          onClick={onConfirm}
          {...testIdProps(testIds.encounters.signConfirm)}
        >
          {confirmLabel}
        </Button>
      </div>
    </dialog>
  );
}

function AddendumForm({
  onSubmit,
}: {
  onSubmit: (body: string) => Promise<void>;
}) {
  const t = useTranslations("encounters");
  const form = useForm<{ body: string }>({ defaultValues: { body: "" } });
  return (
    <Form
      form={form}
      onSubmit={form.handleSubmit(async (values) => {
        await onSubmit(values.body);
        form.reset({ body: "" });
      })}
    >
      <section
        className="space-y-3"
        {...testIdProps(testIds.encounters.addendum)}
      >
        <h2 className="text-lg font-semibold">{t("addendum.title")}</h2>
        <TextAreaField name="body" label={t("addendum.label")} required />
        <Button
          type="submit"
          {...testIdProps(testIds.encounters.addendumSubmit)}
        >
          {t("addendum.submit")}
        </Button>
      </section>
    </Form>
  );
}
