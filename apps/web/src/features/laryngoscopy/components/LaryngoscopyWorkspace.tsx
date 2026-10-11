"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useLocale, useTranslations } from "next-intl";

import { LaryngoscopyComparison } from "./LaryngoscopyComparison";
import { LaryngoscopyScorePanel } from "./LaryngoscopyScorePanel";
import { LaryngoscopyStructureList } from "./LaryngoscopyStructureList";
import { LaryngoscopyVideoPanel } from "./LaryngoscopyVideoPanel";
import { dateTimeLocalToUtcIso } from "@/features/attachments";
import { useCurrentClinicQuery } from "@/features/clinics";
import { AnatomicalMap } from "@/components/clinical/AnatomicalMap/AnatomicalMap";
import { VocalFoldDiagram } from "@/components/clinical/VocalFoldDiagram/VocalFoldDiagram";
import { AutosaveIndicator } from "@/components/forms/AutosaveIndicator";
import { Button } from "@/components/ui/button";
import { larynxMap } from "@/lib/anatomy";
import type { MapSide } from "@/lib/anatomy/types";
import { ApiError } from "@/lib/api/errors";
import type { LaryngoscopyExamRead } from "@/lib/api/generated";
import type { AutosaveStatus } from "@/lib/forms/autosave";
import { formatDate } from "@/lib/i18n/format";
import {
  laryngoscopyExamTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";
import { isoToDateTimeLocal } from "../lib/clock";
import {
  ANESTHESIA_TYPES,
  GLOTTIC_VALUES,
  LESION_FINDINGS,
  MOBILITY_VALUES,
  POSITION_VALUES,
  PROCEDURE_LATERALITIES,
  REINKE_CODE,
  REINKE_GRADES,
  SCOPE_TYPES,
  SETTINGS,
  SUPRAGLOTTIC_VALUES,
  TOLERANCE_VALUES,
  applyMapFinding,
  applyMapNormal,
  applyMapNotExamined,
  applyTemplate,
  draftFromExam,
  draftIssue,
  emptyDraft,
  marksForSide,
  selectPreviousExam,
  templateFocus,
  toCreateBody,
  toUpdateBody,
  type LaryngoscopyDraft,
  type LaryngoscopyTemplate,
  type StructureLaterality,
} from "../lib/draft";
import {
  anesthesiaLabel,
  glotticLabel,
  lateralityLabel,
  mobilityLabel,
  positionLabel,
  recordStatusLabel,
  scopeLabel,
  settingLabel,
  strobeChoiceLabel,
  supraglotticLabel,
  toleranceLabel,
  validationLabel,
} from "../lib/labels";
import {
  useLaryngoscopyValueSet,
  usePatientLaryngoscopies,
  useSaveLaryngoscopy,
  useSignLaryngoscopy,
} from "../hooks/use-laryngoscopy";

type LaryngoscopyWorkspaceProps = {
  patientId: string;
  examId: string | null;
  onExamChange: (examId: string | null) => void;
};

const TEMPLATES: readonly LaryngoscopyTemplate[] = [
  "pre_thyroid",
  "post_thyroid",
  "paralysis",
  "fees",
  "pediatric",
  "tracheostomy",
];

export function LaryngoscopyWorkspace({
  patientId,
  examId,
  onExamChange,
}: LaryngoscopyWorkspaceProps) {
  const t = useTranslations("laryngoscopy");
  const locale = useLocale();
  const list = usePatientLaryngoscopies(patientId);
  const findings = useLaryngoscopyValueSet("laryngoscopy.findings");
  const structures = useLaryngoscopyValueSet("laryngoscopy.structures");
  const lesions = useLaryngoscopyValueSet("laryngoscopy.lesions");
  const thirds = useLaryngoscopyValueSet("laryngoscopy.vf_thirds");
  const surfaces = useLaryngoscopyValueSet("laryngoscopy.vf_surfaces");
  const consistencies = useLaryngoscopyValueSet("fees.consistencies");
  const clinic = useCurrentClinicQuery();
  const save = useSaveLaryngoscopy(patientId);
  const sign = useSignLaryngoscopy(patientId);
  const timeZone = clinic.data?.timezone ?? "UTC";
  const exams = list.data?.items ?? [];
  const selected = exams.find((exam) => exam.publicId === examId) ?? null;
  const readOnly = selected !== null && selected.procedureStatus !== "draft";
  const [side, setSide] = useState<MapSide>("right");
  const [focusId, setFocusId] = useState(larynxMap.regions[0]?.id ?? "");
  const [hint, setHint] = useState<LaryngoscopyTemplate | null>(null);
  const [confirmingSign, setConfirmingSign] = useState(false);
  const [issue, setIssue] = useState<ReturnType<typeof draftIssue>>(null);
  const [autosave, setAutosave] = useState<AutosaveStatus>("idle");
  const [draft, setDraft] = useState<LaryngoscopyDraft>(() =>
    emptyDraft(isoToDateTimeLocal(new Date().toISOString(), "UTC")),
  );
  const [baseline, setBaseline] = useState(() => JSON.stringify(draft));
  const versionRef = useRef(selected?.version ?? 1);
  const loadedKey = useRef<string | null>(null);

  useEffect(() => {
    const key = selected ? `${selected.publicId}:${selected.version}` : "new";
    if (loadedKey.current === key) {
      return;
    }
    loadedKey.current = key;
    const next = selected
      ? draftFromExam(
          selected,
          isoToDateTimeLocal(selected.performedAt, timeZone),
        )
      : emptyDraft(isoToDateTimeLocal(new Date().toISOString(), timeZone));
    versionRef.current = selected?.version ?? 1;
    setDraft(next);
    setBaseline(JSON.stringify(next));
    setIssue(null);
    setAutosave("idle");
  }, [selected, timeZone]);

  const dirty = JSON.stringify(draft) !== baseline;
  const previous = selectPreviousExam(
    exams,
    selected?.publicId ?? null,
    selected?.performedAt ?? null,
  );
  const focusRegion =
    larynxMap.regions.find((region) => region.id === focusId) ??
    larynxMap.regions[0] ??
    null;
  const focusLaterality: StructureLaterality =
    focusRegion?.fixedLaterality === "midline" ? "midline" : side;
  const bodySitePublicId =
    structures.data?.members.find(
      (member) => member.code === focusRegion?.bodySiteCode,
    )?.publicId ?? null;
  const findingOptions = useMemo(
    () =>
      (findings.data?.members ?? []).map((member) => ({
        code: member.code,
        display: member.display,
      })),
    [findings.data?.members],
  );
  const lesionOptions = (lesions.data?.members ?? []).filter((member) =>
    (LESION_FINDINGS as readonly string[]).includes(member.code),
  );

  const persistLatest = useRef<
    (silent: boolean) => Promise<LaryngoscopyExamRead | null>
  >(async () => null);

  useEffect(() => {
    if (!dirty) {
      return;
    }
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = t("dirty");
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [dirty, t]);

  useEffect(() => {
    if (!dirty || readOnly || !selected) {
      return;
    }
    const timer = setTimeout(() => {
      void persistLatest.current(true);
    }, 2000);
    return () => clearTimeout(timer);
  }, [dirty, draft, readOnly, selected]);

  async function persist(
    silent: boolean,
  ): Promise<LaryngoscopyExamRead | null> {
    const performedAtIso = dateTimeLocalToUtcIso(draft.performedAt, timeZone);
    const problem = draftIssue(draft, performedAtIso);
    if (problem) {
      setIssue(problem);
      return null;
    }
    setIssue(null);
    const created = toCreateBody(draft, patientId, performedAtIso);
    const updated = toUpdateBody(draft, versionRef.current, performedAtIso);
    if (!created.ok) {
      setIssue(created.issue);
      return null;
    }
    if (!updated.ok) {
      setIssue(updated.issue);
      return null;
    }
    setAutosave("saving");
    try {
      const savedExam = await save.mutateAsync({
        examId: selected?.publicId ?? null,
        createBody: created.body,
        updateBody: updated.body,
        silent,
      });
      const next = draftFromExam(
        savedExam,
        isoToDateTimeLocal(savedExam.performedAt, timeZone),
      );
      versionRef.current = savedExam.version;
      loadedKey.current = `${savedExam.publicId}:${savedExam.version}`;
      setDraft(next);
      setBaseline(JSON.stringify(next));
      setAutosave("saved");
      if (savedExam.publicId !== examId) {
        onExamChange(savedExam.publicId);
      }
      return savedExam;
    } catch (error) {
      const conflict =
        error instanceof ApiError &&
        (error.status === 409 || error.code.endsWith("version_conflict"));
      setAutosave(conflict ? "conflict" : "error");
      return null;
    }
  }

  persistLatest.current = persist;

  function fillTemplate(template: LaryngoscopyTemplate) {
    setDraft((current) => applyTemplate(current, template));
    setHint(template);
    setFocusId(templateFocus(template));
  }

  if (list.isLoading) {
    return (
      <p
        className="text-sm text-muted-foreground"
        {...testIdProps(testIds.laryngoscopy.loading)}
      >
        {t("loading")}
      </p>
    );
  }
  if (list.isError) {
    return (
      <p
        className="text-sm text-destructive"
        {...testIdProps(testIds.laryngoscopy.error)}
      >
        {t("loadError")}
      </p>
    );
  }

  return (
    <div className="space-y-6" {...testIdProps(testIds.laryngoscopy.root)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">{t("title")}</h2>
        <AutosaveIndicator status={autosave} />
      </div>
      <div className="flex flex-wrap gap-2" aria-label={t("templates.group")}>
        {TEMPLATES.map((template) => (
          <Button
            key={template}
            type="button"
            variant="secondary"
            disabled={readOnly}
            onClick={() => fillTemplate(template)}
            {...testIdProps(templateTestId(template))}
          >
            {templateLabel(t, template)}
          </Button>
        ))}
      </div>
      {hint ? (
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.laryngoscopy.templateHint)}
        >
          {templateHint(t, hint)}
        </p>
      ) : null}
      <div className="grid gap-6 lg:grid-cols-[16rem_minmax(0,1fr)]">
        <aside
          className="space-y-2"
          {...testIdProps(testIds.laryngoscopy.list)}
        >
          <h3 className="text-sm font-semibold">{t("listTitle")}</h3>
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              loadedKey.current = null;
              onExamChange(null);
            }}
            {...testIdProps(testIds.laryngoscopy.newExam)}
          >
            {t("newExam")}
          </Button>
          {exams.length === 0 ? (
            <p
              className="text-sm text-muted-foreground"
              {...testIdProps(testIds.laryngoscopy.empty)}
            >
              {t("empty")}
            </p>
          ) : (
            exams.map((exam) => (
              <button
                key={exam.publicId}
                type="button"
                className="block w-full rounded-xl border border-border px-3 py-2 text-start text-sm"
                onClick={() => onExamChange(exam.publicId)}
                {...testIdProps(laryngoscopyExamTestId(exam.publicId))}
              >
                {formatDate(exam.performedAt, locale)}
                <span className="ms-2 text-xs text-muted-foreground">
                  {recordStatusLabel(t, exam.procedureStatus)}
                </span>
              </button>
            ))
          )}
        </aside>
        <div className="space-y-6">
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-1 text-sm">
              {t("fields.performedAt")}
              <input
                type="datetime-local"
                className="flex h-10 w-full rounded-lg border border-input bg-card px-3 text-sm"
                disabled={readOnly}
                value={draft.performedAt}
                onChange={(event) =>
                  setDraft({ ...draft, performedAt: event.target.value })
                }
                {...testIdProps(testIds.laryngoscopy.performedAt)}
              />
            </label>
            <label className="space-y-1 text-sm">
              {t("fields.scope")}
              <select
                className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                disabled={readOnly}
                value={draft.scopeType}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    scopeType: event.target
                      .value as LaryngoscopyDraft["scopeType"],
                  })
                }
                {...testIdProps(testIds.laryngoscopy.scope)}
              >
                {SCOPE_TYPES.map((value) => (
                  <option key={value} value={value}>
                    {scopeLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              {t("fields.anesthesia")}
              <select
                className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                disabled={readOnly}
                value={draft.anesthesia}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    anesthesia: event.target
                      .value as LaryngoscopyDraft["anesthesia"],
                  })
                }
                {...testIdProps(testIds.laryngoscopy.anesthesia)}
              >
                {ANESTHESIA_TYPES.map((value) => (
                  <option key={value} value={value}>
                    {anesthesiaLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              {t("fields.setting")}
              <select
                className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                disabled={readOnly}
                value={draft.setting}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    setting: event.target.value as LaryngoscopyDraft["setting"],
                  })
                }
                {...testIdProps(testIds.laryngoscopy.setting)}
              >
                {SETTINGS.map((value) => (
                  <option key={value} value={value}>
                    {settingLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              {t("fields.laterality")}
              <select
                className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                disabled={readOnly}
                value={draft.laterality}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    laterality: event.target
                      .value as LaryngoscopyDraft["laterality"],
                  })
                }
                {...testIdProps(testIds.laryngoscopy.laterality)}
              >
                {PROCEDURE_LATERALITIES.map((value) => (
                  <option key={value} value={value}>
                    {lateralityLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              {t("fields.tolerance")}
              <select
                className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                disabled={readOnly}
                value={draft.tolerance}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    tolerance: event.target
                      .value as LaryngoscopyDraft["tolerance"],
                  })
                }
                {...testIdProps(testIds.laryngoscopy.tolerance)}
              >
                <option value="">{toleranceLabel(t, "")}</option>
                {TOLERANCE_VALUES.map((value) => (
                  <option key={value} value={value}>
                    {toleranceLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              {t("fields.instrument")}
              <input
                className="flex h-10 w-full rounded-lg border border-input bg-card px-3 text-sm"
                disabled={readOnly}
                value={draft.instrument}
                onChange={(event) =>
                  setDraft({ ...draft, instrument: event.target.value })
                }
                {...testIdProps(testIds.laryngoscopy.instrument)}
              />
            </label>
            <label className="space-y-1 text-sm sm:col-span-2">
              {t("fields.indication")}
              <textarea
                className="min-h-20 w-full rounded-lg border border-input bg-card px-3 py-2 text-sm"
                disabled={readOnly}
                value={draft.indicationText}
                onChange={(event) =>
                  setDraft({ ...draft, indicationText: event.target.value })
                }
                {...testIdProps(testIds.laryngoscopy.indication)}
              />
            </label>
            <label className="space-y-1 text-sm sm:col-span-2">
              {t("fields.conclusion")}
              <textarea
                className="min-h-24 w-full rounded-lg border border-input bg-card px-3 py-2 text-sm"
                disabled={readOnly}
                value={draft.conclusionText}
                onChange={(event) =>
                  setDraft({ ...draft, conclusionText: event.target.value })
                }
                {...testIdProps(testIds.laryngoscopy.conclusion)}
              />
            </label>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <FoldFields
              title={t("fields.rightFold")}
              fold={draft.vocalFoldRight}
              readOnly={readOnly}
              mobilityTestId={testIds.laryngoscopy.mobilityRight}
              positionTestId={testIds.laryngoscopy.positionRight}
              onChange={(fold) => setDraft({ ...draft, vocalFoldRight: fold })}
            />
            <FoldFields
              title={t("fields.leftFold")}
              fold={draft.vocalFoldLeft}
              readOnly={readOnly}
              mobilityTestId={testIds.laryngoscopy.mobilityLeft}
              positionTestId={testIds.laryngoscopy.positionLeft}
              onChange={(fold) => setDraft({ ...draft, vocalFoldLeft: fold })}
            />
            <label className="space-y-1 text-sm">
              {t("fields.glottic")}
              <select
                className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                disabled={readOnly}
                value={draft.glotticClosure}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    glotticClosure: event.target
                      .value as LaryngoscopyDraft["glotticClosure"],
                  })
                }
                {...testIdProps(testIds.laryngoscopy.glottic)}
              >
                {GLOTTIC_VALUES.map((value) => (
                  <option key={value} value={value}>
                    {glotticLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              {t("fields.supraglottic")}
              <select
                className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                disabled={readOnly}
                value={draft.supraglotticPattern}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    supraglotticPattern: event.target
                      .value as LaryngoscopyDraft["supraglotticPattern"],
                  })
                }
                {...testIdProps(testIds.laryngoscopy.supraglottic)}
              >
                <option value="">{supraglotticLabel(t, "")}</option>
                {SUPRAGLOTTIC_VALUES.map((value) => (
                  <option key={value} value={value}>
                    {supraglotticLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {focusRegion ? (
            <AnatomicalMap
              definition={larynxMap}
              selectedSide={side}
              marks={marksForSide(draft, side)}
              findingsByValueSet={{
                "laryngoscopy.findings": findingOptions,
              }}
              findingsLoading={findings.isLoading}
              onSelectedSideChange={setSide}
              onMarkNormal={(region) =>
                setDraft((current) => applyMapNormal(current, region, side))
              }
              onSelectFinding={(region, code) =>
                setDraft((current) =>
                  applyMapFinding(current, region, side, code),
                )
              }
              onMarkNotExamined={(region) =>
                setDraft((current) =>
                  applyMapNotExamined(current, region, side),
                )
              }
              onAttachPhoto={(region) => setFocusId(region.id)}
            />
          ) : null}
          <LaryngoscopyStructureList
            draft={draft}
            regions={larynxMap.regions}
            findings={findings.data?.members ?? []}
            readOnly={readOnly}
            onChange={setDraft}
            onFocus={(regionId, laterality) => {
              setFocusId(regionId);
              if (laterality === "right" || laterality === "left") {
                setSide(laterality);
              }
            }}
          />
          <VocalFoldDiagram
            lesions={draft.lesions}
            thirds={thirds.data?.members ?? []}
            surfaces={surfaces.data?.members ?? []}
            findings={lesionOptions}
            reinkeCode={REINKE_CODE}
            reinkeGrades={REINKE_GRADES}
            readOnly={readOnly}
            onAdd={(lesion) =>
              setDraft((current) => ({
                ...current,
                lesions: [...current.lesions, lesion],
              }))
            }
            onChange={(index, lesion) =>
              setDraft((current) => ({
                ...current,
                lesions: current.lesions.map((row, rowIndex) =>
                  rowIndex === index ? lesion : row,
                ),
              }))
            }
            onRemove={(index) =>
              setDraft((current) => ({
                ...current,
                lesions: current.lesions.filter(
                  (_row, rowIndex) => rowIndex !== index,
                ),
              }))
            }
          />
          <StrobeFields draft={draft} readOnly={readOnly} onChange={setDraft} />
          <LaryngoscopyScorePanel
            draft={draft}
            saved={selected}
            consistencies={consistencies.data?.members ?? []}
            residueSites={(structures.data?.members ?? []).filter((member) =>
              [
                "ANAT.LARYNX.VALLECULA",
                "ANAT.LARYNX.PYRIFORM",
                "ANAT.LARYNX.POST_CRICOID",
                "ANAT.LARYNX.VOCAL_FOLD",
                "ANAT.LARYNX.VESTIBULE",
              ].includes(member.code),
            )}
            readOnly={readOnly}
            onChange={setDraft}
          />
          <LaryngoscopyComparison
            draft={draft}
            previous={previous}
            exams={exams}
          />
          <LaryngoscopyVideoPanel
            patientId={patientId}
            procedureId={selected?.procedureId ?? null}
            previousProcedureId={previous?.procedureId ?? null}
            bodySitePublicId={bodySitePublicId}
            laterality={focusLaterality}
            readOnly={readOnly}
          />
          {issue ? (
            <p
              className="text-sm text-destructive"
              {...testIdProps(testIds.laryngoscopy.validation)}
            >
              {validationLabel(t, issue)}
            </p>
          ) : null}
          {autosave === "conflict" ? (
            <div
              className="flex items-center gap-3"
              {...testIdProps(testIds.laryngoscopy.conflict)}
            >
              <p className="text-sm text-destructive">{t("conflict")}</p>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  loadedKey.current = null;
                  void list.refetch();
                }}
                {...testIdProps(testIds.laryngoscopy.reload)}
              >
                {t("actions.reload")}
              </Button>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              disabled={readOnly || save.isPending}
              onClick={() => void persist(false)}
              {...testIdProps(testIds.laryngoscopy.save)}
            >
              {t("actions.save")}
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={readOnly || !selected || sign.isPending}
              onClick={() => setConfirmingSign(true)}
              {...testIdProps(testIds.laryngoscopy.sign)}
            >
              {t("actions.sign")}
            </Button>
          </div>
          {confirmingSign ? (
            <div className="flex flex-wrap gap-2 rounded-xl border border-border p-3">
              <Button
                type="button"
                disabled={sign.isPending}
                onClick={() => {
                  void (async () => {
                    const savedExam = dirty ? await persist(true) : selected;
                    if (!savedExam) {
                      return;
                    }
                    await sign.mutateAsync(savedExam.procedureId);
                    setConfirmingSign(false);
                    loadedKey.current = null;
                  })();
                }}
                {...testIdProps(testIds.laryngoscopy.confirmSign)}
              >
                {t("actions.confirmSign")}
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setConfirmingSign(false)}
                {...testIdProps(testIds.laryngoscopy.cancelSign)}
              >
                {t("actions.cancelSign")}
              </Button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function FoldFields({
  title,
  fold,
  readOnly,
  mobilityTestId,
  positionTestId,
  onChange,
}: {
  title: string;
  fold: LaryngoscopyDraft["vocalFoldRight"];
  readOnly: boolean;
  mobilityTestId: string;
  positionTestId: string;
  onChange: (fold: LaryngoscopyDraft["vocalFoldRight"]) => void;
}) {
  const t = useTranslations("laryngoscopy");
  return (
    <fieldset className="space-y-2 rounded-xl border border-border p-3">
      <legend className="text-sm font-medium">{title}</legend>
      <label className="space-y-1 text-sm">
        {t("fields.mobility")}
        <select
          className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
          disabled={readOnly}
          value={fold.mobility}
          onChange={(event) => {
            const mobility = event.target
              .value as LaryngoscopyDraft["vocalFoldRight"]["mobility"];
            onChange({
              mobility,
              position: mobility === "immobile" ? fold.position : "",
            });
          }}
          {...testIdProps(mobilityTestId)}
        >
          {MOBILITY_VALUES.map((value) => (
            <option key={value} value={value}>
              {mobilityLabel(t, value)}
            </option>
          ))}
        </select>
      </label>
      {fold.mobility === "immobile" ? (
        <label className="space-y-1 text-sm">
          {t("fields.position")}
          <select
            className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
            disabled={readOnly}
            value={fold.position}
            onChange={(event) =>
              onChange({
                ...fold,
                position: event.target
                  .value as LaryngoscopyDraft["vocalFoldRight"]["position"],
              })
            }
            {...testIdProps(positionTestId)}
          >
            <option value="">{positionLabel(t, "")}</option>
            {POSITION_VALUES.map((value) => (
              <option key={value} value={value}>
                {positionLabel(t, value)}
              </option>
            ))}
          </select>
        </label>
      ) : null}
    </fieldset>
  );
}

function StrobeFields({
  draft,
  readOnly,
  onChange,
}: {
  draft: LaryngoscopyDraft;
  readOnly: boolean;
  onChange: (draft: LaryngoscopyDraft) => void;
}) {
  const t = useTranslations("laryngoscopy");
  const strobe = draft.stroboscopy;
  return (
    <section className="space-y-3">
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          disabled={readOnly}
          checked={draft.includeStroboscopy}
          onChange={(event) =>
            onChange({ ...draft, includeStroboscopy: event.target.checked })
          }
          {...testIdProps(testIds.laryngoscopy.stroboscopyToggle)}
        />
        {t("strobe.include")}
      </label>
      {draft.includeStroboscopy ? (
        <div className="grid gap-3 sm:grid-cols-2">
          <h3 className="text-sm font-semibold sm:col-span-2">
            {t("strobe.title")}
          </h3>
          {(
            [
              ["symmetry", ["symmetric", "asymmetric"]],
              ["periodicity", ["regular", "irregular"]],
              ["amplitudeRight", ["normal", "reduced", "absent"]],
              ["amplitudeLeft", ["normal", "reduced", "absent"]],
              ["mucosalWaveRight", ["normal", "reduced", "absent"]],
              ["mucosalWaveLeft", ["normal", "reduced", "absent"]],
              [
                "phaseClosure",
                [
                  "",
                  "normal",
                  "predominantly_open",
                  "predominantly_closed",
                  "always_open",
                ],
              ],
              ["phaseSymmetry", ["", "symmetric", "asymmetric"]],
              [
                "verticalLevel",
                [
                  "",
                  "on_plane",
                  "off_plane_right_lower",
                  "off_plane_left_lower",
                ],
              ],
              [
                "nonVibratingSegment",
                ["", "none", "right", "left", "bilateral"],
              ],
            ] as const
          ).map(([field, values]) => (
            <label key={field} className="space-y-1 text-sm">
              {strobeFieldLabel(t, field)}
              <select
                className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                disabled={readOnly}
                value={strobe[field] ?? ""}
                onChange={(event) =>
                  onChange({
                    ...draft,
                    stroboscopy: {
                      ...strobe,
                      [field]: event.target.value,
                    },
                  })
                }
              >
                {values.map((value) => (
                  <option key={value || "unset"} value={value}>
                    {strobeChoiceLabel(t, field, value)}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function strobeFieldLabel(
  t: ReturnType<typeof useTranslations<"laryngoscopy">>,
  field: string,
): string {
  switch (field) {
    case "symmetry":
      return t("strobe.symmetry");
    case "periodicity":
      return t("strobe.periodicity");
    case "amplitudeRight":
      return t("strobe.amplitudeRight");
    case "amplitudeLeft":
      return t("strobe.amplitudeLeft");
    case "mucosalWaveRight":
      return t("strobe.waveRight");
    case "mucosalWaveLeft":
      return t("strobe.waveLeft");
    case "phaseClosure":
      return t("strobe.phaseClosure");
    case "phaseSymmetry":
      return t("strobe.phaseSymmetry");
    case "verticalLevel":
      return t("strobe.vertical");
    case "nonVibratingSegment":
      return t("strobe.nonVibrating");
    default:
      return t("strobe.title");
  }
}

function templateTestId(template: LaryngoscopyTemplate): string {
  switch (template) {
    case "pre_thyroid":
      return testIds.laryngoscopy.templatePreThyroid;
    case "post_thyroid":
      return testIds.laryngoscopy.templatePostThyroid;
    case "paralysis":
      return testIds.laryngoscopy.templateParalysis;
    case "fees":
      return testIds.laryngoscopy.templateFees;
    case "pediatric":
      return testIds.laryngoscopy.templatePediatric;
    case "tracheostomy":
      return testIds.laryngoscopy.templateTracheostomy;
    default: {
      const _exhaustive: never = template;
      return _exhaustive;
    }
  }
}

function templateLabel(
  t: ReturnType<typeof useTranslations<"laryngoscopy">>,
  template: LaryngoscopyTemplate,
): string {
  switch (template) {
    case "pre_thyroid":
      return t("templates.preThyroid");
    case "post_thyroid":
      return t("templates.postThyroid");
    case "paralysis":
      return t("templates.paralysis");
    case "fees":
      return t("templates.fees");
    case "pediatric":
      return t("templates.pediatric");
    case "tracheostomy":
      return t("templates.tracheostomy");
    default: {
      const _exhaustive: never = template;
      return _exhaustive;
    }
  }
}

function templateHint(
  t: ReturnType<typeof useTranslations<"laryngoscopy">>,
  template: LaryngoscopyTemplate,
): string {
  switch (template) {
    case "pre_thyroid":
      return t("templates.preThyroidHint");
    case "post_thyroid":
      return t("templates.postThyroidHint");
    case "paralysis":
      return t("templates.paralysisHint");
    case "fees":
      return t("templates.feesHint");
    case "pediatric":
      return t("templates.pediatricHint");
    case "tracheostomy":
      return t("templates.tracheostomyHint");
    default: {
      const _exhaustive: never = template;
      return _exhaustive;
    }
  }
}
