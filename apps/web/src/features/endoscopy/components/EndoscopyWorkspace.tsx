"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useLocale, useTranslations } from "next-intl";

import { EndoscopyComparison } from "./EndoscopyComparison";
import { EndoscopyMediaPanel } from "./EndoscopyMediaPanel";
import { EndoscopyScorePanel } from "./EndoscopyScorePanel";
import { EndoscopyStructureList } from "./EndoscopyStructureList";
import { dateTimeLocalToUtcIso } from "@/features/attachments";
import {
  useClinicalSettingsQuery,
  useCurrentClinicQuery,
} from "@/features/clinics";
import { AnatomicalMap } from "@/components/clinical/AnatomicalMap/AnatomicalMap";
import { AutosaveIndicator } from "@/components/forms/AutosaveIndicator";
import { Button } from "@/components/ui/button";
import { nasalEndoscopyMap } from "@/lib/anatomy";
import type { MapSide } from "@/lib/anatomy/types";
import { ApiError } from "@/lib/api/errors";
import type { EndoscopyExamRead } from "@/lib/api/generated";
import type { AutosaveStatus } from "@/lib/forms/autosave";
import { formatDate } from "@/lib/i18n/format";
import { endoscopyExamTestId, testIdProps, testIds } from "@/lib/test/test-id";
import { isoToDateTimeLocal } from "../lib/clock";
import {
  ANESTHESIA_TYPES,
  PROCEDURE_LATERALITIES,
  SCOPE_TYPES,
  SETTINGS,
  TOLERANCE_VALUES,
  applyMapFinding,
  applyMapNormal,
  applyMapNotExamined,
  applyTemplate,
  draftFromExam,
  draftIssue,
  emptyDraft,
  isPolypScale,
  marksForSide,
  selectPreviousExam,
  templateFocus,
  toCreateBody,
  toUpdateBody,
  type EndoscopyDraft,
  type EndoscopyTemplate,
  type PolypScaleName,
  type StructureLaterality,
} from "../lib/draft";
import {
  anesthesiaLabel,
  lateralityLabel,
  recordStatusLabel,
  scopeLabel,
  settingLabel,
  toleranceLabel,
  validationLabel,
} from "../lib/labels";
import {
  useEndoscopyValueSet,
  usePatientEndoscopies,
  useSaveEndoscopy,
  useSignProcedure,
} from "../hooks/use-endoscopy";

type EndoscopyWorkspaceProps = {
  patientId: string;
  examId: string | null;
  onExamChange: (examId: string | null) => void;
};

export function EndoscopyWorkspace({
  patientId,
  examId,
  onExamChange,
}: EndoscopyWorkspaceProps) {
  const t = useTranslations("endoscopy");
  const locale = useLocale();
  const list = usePatientEndoscopies(patientId);
  const findings = useEndoscopyValueSet("endoscopy.findings");
  const structures = useEndoscopyValueSet("endoscopy.structures");
  const settings = useClinicalSettingsQuery();
  const clinic = useCurrentClinicQuery();
  const save = useSaveEndoscopy(patientId);
  const sign = useSignProcedure(patientId);
  const timeZone = clinic.data?.timezone ?? "UTC";
  const exams = list.data?.items ?? [];
  const selected = exams.find((exam) => exam.publicId === examId) ?? null;
  const readOnly = selected !== null && selected.procedureStatus !== "draft";
  const scale = resolveScale(selected, settings.data?.items);
  const [side, setSide] = useState<MapSide>("right");
  const [focusId, setFocusId] = useState(
    nasalEndoscopyMap.regions[0]?.id ?? "",
  );
  const [hint, setHint] = useState<EndoscopyTemplate | null>(null);
  const [confirmingSign, setConfirmingSign] = useState(false);
  const [issue, setIssue] = useState<ReturnType<typeof draftIssue>>(null);
  const [autosave, setAutosave] = useState<AutosaveStatus>("idle");
  const [draft, setDraft] = useState<EndoscopyDraft>(() =>
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
    nasalEndoscopyMap.regions.find((region) => region.id === focusId) ??
    nasalEndoscopyMap.regions[0] ??
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

  const persistLatest = useRef<
    (silent: boolean) => Promise<EndoscopyExamRead | null>
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
    if (!dirty || readOnly || !selected || scale === null) {
      return;
    }
    const timer = setTimeout(() => {
      void persistLatest.current(true);
    }, 2000);
    return () => clearTimeout(timer);
  }, [dirty, draft, readOnly, selected, scale]);

  async function persist(silent: boolean): Promise<EndoscopyExamRead | null> {
    if (scale === null) {
      return null;
    }
    const performedAtIso = dateTimeLocalToUtcIso(draft.performedAt, timeZone);
    const problem = draftIssue(draft, scale, performedAtIso);
    if (problem) {
      setIssue(problem);
      return null;
    }
    setIssue(null);
    const created = toCreateBody(draft, patientId, scale, performedAtIso);
    const updated = toUpdateBody(
      draft,
      versionRef.current,
      scale,
      performedAtIso,
    );
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

  function fillTemplate(template: EndoscopyTemplate) {
    setDraft((current) => applyTemplate(current, template));
    setHint(template);
    const focus = templateFocus(template);
    if (focus) {
      setFocusId(focus);
    }
  }

  if (list.isLoading) {
    return (
      <p
        className="text-sm text-muted-foreground"
        {...testIdProps(testIds.endoscopy.loading)}
      >
        {t("loading")}
      </p>
    );
  }
  if (list.isError) {
    return (
      <p
        className="text-sm text-destructive"
        {...testIdProps(testIds.endoscopy.error)}
      >
        {t("loadError")}
      </p>
    );
  }

  return (
    <div className="space-y-6" {...testIdProps(testIds.endoscopy.root)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">{t("title")}</h2>
        <AutosaveIndicator status={autosave} />
      </div>
      <div className="flex flex-wrap gap-2" aria-label={t("templates.group")}>
        <Button
          type="button"
          variant="secondary"
          disabled={readOnly}
          onClick={() => fillTemplate("normal")}
          {...testIdProps(testIds.endoscopy.templateNormal)}
        >
          {t("templates.normal")}
        </Button>
        <Button
          type="button"
          variant="secondary"
          disabled={readOnly}
          onClick={() => fillTemplate("post_fess")}
          {...testIdProps(testIds.endoscopy.templatePostFess)}
        >
          {t("templates.postFess")}
        </Button>
        <Button
          type="button"
          variant="secondary"
          disabled={readOnly}
          onClick={() => fillTemplate("epistaxis")}
          {...testIdProps(testIds.endoscopy.templateEpistaxis)}
        >
          {t("templates.epistaxis")}
        </Button>
      </div>
      {hint === "post_fess" ? (
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.endoscopy.templateHint)}
        >
          {t("templates.postFessHint")}
        </p>
      ) : null}
      {hint === "epistaxis" ? (
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.endoscopy.templateHint)}
        >
          {t("templates.epistaxisHint")}
        </p>
      ) : null}
      <div className="grid gap-6 lg:grid-cols-[16rem_minmax(0,1fr)]">
        <aside className="space-y-2" {...testIdProps(testIds.endoscopy.list)}>
          <h3 className="text-sm font-semibold">{t("listTitle")}</h3>
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              loadedKey.current = null;
              onExamChange(null);
            }}
            {...testIdProps(testIds.endoscopy.newExam)}
          >
            {t("newExam")}
          </Button>
          {exams.length === 0 ? (
            <p
              className="text-sm text-muted-foreground"
              {...testIdProps(testIds.endoscopy.empty)}
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
                {...testIdProps(endoscopyExamTestId(exam.publicId))}
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
                {...testIdProps(testIds.endoscopy.performedAt)}
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
                      .value as EndoscopyDraft["scopeType"],
                  })
                }
                {...testIdProps(testIds.endoscopy.scope)}
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
                      .value as EndoscopyDraft["anesthesia"],
                  })
                }
                {...testIdProps(testIds.endoscopy.anesthesia)}
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
                    setting: event.target.value as EndoscopyDraft["setting"],
                  })
                }
                {...testIdProps(testIds.endoscopy.setting)}
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
                      .value as EndoscopyDraft["laterality"],
                  })
                }
                {...testIdProps(testIds.endoscopy.laterality)}
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
                      .value as EndoscopyDraft["tolerance"],
                  })
                }
                {...testIdProps(testIds.endoscopy.tolerance)}
              >
                <option value="">{toleranceLabel(t, "")}</option>
                {TOLERANCE_VALUES.map((value) => (
                  <option key={value} value={value}>
                    {toleranceLabel(t, value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-sm sm:col-span-2">
              <input
                type="checkbox"
                disabled={readOnly}
                checked={draft.decongestantUsed}
                onChange={(event) =>
                  setDraft({ ...draft, decongestantUsed: event.target.checked })
                }
                {...testIdProps(testIds.endoscopy.decongestant)}
              />
              {t("fields.decongestant")}
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
                {...testIdProps(testIds.endoscopy.instrument)}
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
                {...testIdProps(testIds.endoscopy.indication)}
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
                {...testIdProps(testIds.endoscopy.conclusion)}
              />
            </label>
          </div>
          {focusRegion ? (
            <AnatomicalMap
              definition={nasalEndoscopyMap}
              selectedSide={side}
              marks={marksForSide(draft, side)}
              findingsByValueSet={{
                [nasalEndoscopyMap.regions[0]?.valueSetCode ??
                "endoscopy.findings"]: findingOptions,
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
          <EndoscopyStructureList
            draft={draft}
            regions={nasalEndoscopyMap.regions}
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
          <EndoscopyScorePanel
            draft={draft}
            scale={scale}
            saved={selected}
            readOnly={readOnly}
            onChange={setDraft}
          />
          <EndoscopyComparison
            draft={draft}
            previous={previous}
            exams={exams}
            findings={findings.data?.members ?? []}
          />
          <EndoscopyMediaPanel
            patientId={patientId}
            bodySiteCode={focusRegion?.bodySiteCode ?? null}
            bodySitePublicId={bodySitePublicId}
            laterality={focusLaterality}
            readOnly={readOnly}
          />
          {issue ? (
            <p
              className="text-sm text-destructive"
              {...testIdProps(testIds.endoscopy.validation)}
            >
              {validationLabel(t, issue)}
            </p>
          ) : null}
          {autosave === "conflict" ? (
            <div
              className="flex items-center gap-3"
              {...testIdProps(testIds.endoscopy.conflict)}
            >
              <p className="text-sm text-destructive">{t("conflict")}</p>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  loadedKey.current = null;
                  void list.refetch();
                }}
                {...testIdProps(testIds.endoscopy.reload)}
              >
                {t("actions.reload")}
              </Button>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              disabled={readOnly || save.isPending || scale === null}
              onClick={() => void persist(false)}
              {...testIdProps(testIds.endoscopy.save)}
            >
              {t("actions.save")}
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={readOnly || !selected || sign.isPending}
              onClick={() => setConfirmingSign(true)}
              {...testIdProps(testIds.endoscopy.sign)}
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
                {...testIdProps(testIds.endoscopy.confirmSign)}
              >
                {t("actions.confirmSign")}
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setConfirmingSign(false)}
                {...testIdProps(testIds.endoscopy.cancelSign)}
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

function resolveScale(
  exam: EndoscopyExamRead | null,
  items: { key: string; value: unknown }[] | undefined,
): PolypScaleName | null {
  if (exam && isPolypScale(exam.polypScale)) {
    return exam.polypScale;
  }
  const raw = items?.find((item) => item.key === "polyp_scale")?.value;
  if (typeof raw === "string" && isPolypScale(raw)) {
    return raw;
  }
  return null;
}
