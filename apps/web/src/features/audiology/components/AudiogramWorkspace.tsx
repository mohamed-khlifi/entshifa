"use client";

import { useLocale, useTranslations } from "next-intl";
import {
  cloneElement,
  useEffect,
  useMemo,
  useRef,
  useState,
  type InputHTMLAttributes,
  type ReactElement,
  type ReactNode,
} from "react";

import { AudiogramChart } from "./AudiogramChart/AudiogramChart";
import {
  applyPlotToCells,
  AudiogramGrid,
} from "./AudiogramChart/AudiogramGrid";
import { AudiologyDashboard } from "./AudiologyDashboard";
import { ComparisonOverlay } from "./ComparisonOverlay";
import { useCurrentClinicQuery } from "@/features/clinics";
import { usePatientQuery } from "@/features/patients";
import { ApiError } from "@/lib/api/errors";
import { formatDate } from "@/lib/i18n/format";
import { Permission } from "@/lib/permissions";
import { audiogramRowTestId, testIdProps, testIds } from "@/lib/test/test-id";
import { usePermission } from "@/providers/permission-provider";

import {
  useAudiogramCompare,
  useFinalizeAudiogram,
  useSaveAudiogram,
} from "../hooks/use-audiology";
import { isoToDateTimeLocal } from "../lib/clock";
import {
  cycleActiveEar,
  draftFromExam,
  draftIssues,
  emptyDraft,
  metricsFromRead,
  toggleActiveMasked,
  toWrite,
} from "../lib/draft";
import type { AudiogramDraft } from "../types/audiology.types";
import {
  earLabel,
  methodLabel,
  ptaFormulaLabel,
  reliabilityLabel,
  transducerLabel,
} from "../lib/labels";
import { RELIABILITY_VALUES, TEST_METHODS, TRANSDUCERS } from "../constants";
import type { OverlaySeries } from "../types/audiology.types";
import {
  frequenciesForChart,
  thresholdsFromCells,
  thresholdsToChartPoints,
} from "../utils/audiogram.utils";

type AudiogramWorkspaceProps = {
  patientId: string;
  audiogramId: string | null;
  onAudiogramChange: (audiogramId: string | null) => void;
};

export function AudiogramWorkspace({
  patientId,
  audiogramId,
  onAudiogramChange,
}: AudiogramWorkspaceProps) {
  const t = useTranslations("audiology");
  const locale = useLocale();
  const canEnter = usePermission(Permission.AUDIOLOGY_ENTER);
  const canInterpret = usePermission(Permission.AUDIOLOGY_INTERPRET);
  const clinic = useCurrentClinicQuery();
  const patient = usePatientQuery(patientId);
  const timeZone = clinic.data?.timezone ?? "UTC";
  const { list, overlayCandidates, idempotencyKey, resetIdempotencyKey } =
    useAudiogramCompare(patientId, audiogramId);
  const save = useSaveAudiogram(patientId);
  const finalize = useFinalizeAudiogram(patientId);
  const [draft, setDraft] = useState<AudiogramDraft>(() =>
    emptyDraft(localNow()),
  );
  const [baseline, setBaseline] = useState<string | null>(null);
  const [overlayIds, setOverlayIds] = useState<Set<string>>(() => new Set());
  const [confirmFinalize, setConfirmFinalize] = useState(false);
  const [viewMode, setViewMode] = useState<"dashboard" | "entry">("dashboard");
  const [issues, setIssues] = useState<string[]>([]);
  const [conflict, setConflict] = useState(false);
  const loadedKey = useRef<string | null>(null);

  const selected = list.data?.items.find((row) => row.publicId === audiogramId);
  const readOnly = draft.status === "final" || !canEnter;
  const dirty = baseline !== null && JSON.stringify(draft) !== baseline;

  useEffect(() => {
    if (clinic.isLoading) {
      return;
    }
    const key = selected
      ? `${selected.publicId}:${selected.version}:${timeZone}`
      : audiogramId
        ? "pending"
        : `new:${timeZone}`;
    if (loadedKey.current === key) {
      return;
    }
    loadedKey.current = key;
    if (!selected) {
      if (audiogramId) {
        return;
      }
      const next = emptyDraft(localNow());
      setDraft(next);
      setBaseline(JSON.stringify(next));
      setIssues([]);
      setConflict(false);
      setOverlayIds(new Set());
      return;
    }
    const next = draftFromExam(
      selected,
      isoToDateTimeLocal(selected.performedAt, timeZone),
    );
    setDraft(next);
    setBaseline(JSON.stringify(next));
    setIssues([]);
    setConflict(false);
  }, [audiogramId, clinic.isLoading, selected, timeZone]);

  const persistLatest = useRef<(silent: boolean) => Promise<void>>(
    async () => undefined,
  );

  useEffect(() => {
    if (!dirty || readOnly || draft.version === null) {
      return;
    }
    const handle = window.setTimeout(() => {
      void persistLatest.current(true);
    }, 2000);
    return () => window.clearTimeout(handle);
  }, [dirty, draft, readOnly]);

  const frequencies = useMemo(
    () => frequenciesForChart(draft.showExtendedHigh),
    [draft.showExtendedHigh],
  );

  const currentPoints = useMemo(
    () => thresholdsToChartPoints(thresholdsFromCells(draft.cells)),
    [draft.cells],
  );

  const overlays: OverlaySeries[] = useMemo(() => {
    return overlayCandidates
      .filter((row) => overlayIds.has(row.publicId))
      .map((row) => ({
        publicId: row.publicId,
        performedAt: row.performedAt,
        isBaseline: row.isBaseline,
        thresholds: row.thresholds,
      }));
  }, [overlayCandidates, overlayIds]);

  const overlayOptions: OverlaySeries[] = useMemo(() => {
    return overlayCandidates.map((row) => ({
      publicId: row.publicId,
      performedAt: row.performedAt,
      isBaseline: row.isBaseline,
      thresholds: row.thresholds,
    }));
  }, [overlayCandidates]);

  async function persist(silent: boolean) {
    const found = draftIssues(draft);
    if (found.length > 0) {
      if (!silent) {
        setIssues(found);
      }
      return;
    }
    const body = toWrite(draft, patientId, timeZone, { canInterpret });
    if (!body) {
      if (!silent) {
        setIssues(["performedAt"]);
      }
      return;
    }
    try {
      const saved = await save.mutateAsync({
        audiogramId,
        createBody: body.create,
        updateBody: body.update,
        idempotencyKey,
        silent,
      });
      const next: AudiogramDraft = {
        ...draft,
        version: saved.version,
        publicId: saved.publicId,
        status: saved.status === "final" ? "final" : "draft",
        metrics: metricsFromRead(saved),
      };
      loadedKey.current = `${saved.publicId}:${saved.version}:${timeZone}`;
      setDraft(next);
      setBaseline(JSON.stringify(next));
      setIssues([]);
      setConflict(false);
      if (saved.publicId !== audiogramId) {
        onAudiogramChange(saved.publicId);
      }
    } catch (error) {
      const isConflict =
        error instanceof ApiError &&
        (error.status === 409 || error.code.endsWith("version_conflict"));
      if (isConflict) {
        setConflict(true);
      } else if (!silent) {
        throw error;
      }
    }
  }
  persistLatest.current = persist;

  if (list.isLoading) {
    return (
      <p {...testIdProps(testIds.audiology.loading)}>{t("state.loading")}</p>
    );
  }
  if (list.isError) {
    return <p {...testIdProps(testIds.audiology.error)}>{t("state.error")}</p>;
  }

  const patientName = patient.data
    ? `${patient.data.firstName} ${patient.data.lastName}`
    : "";

  return (
    <div className="space-y-6" {...testIdProps(testIds.audiology.root)}>
      <style>{`@media print { body * { visibility: hidden !important; } .audiogram-print-sheet, .audiogram-print-sheet * { visibility: visible !important; } .audiogram-print-sheet { position: absolute; inset: 0; background: white; } }`}</style>
      <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
        <h2 className="text-xl font-semibold">{t("title")}</h2>
        {canEnter ? (
          <button
            type="button"
            className="rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
            onClick={() => {
              resetIdempotencyKey();
              setDraft(emptyDraft(localNow()));
              setIssues([]);
              setOverlayIds(new Set());
              onAudiogramChange(null);
            }}
            {...testIdProps(testIds.audiology.newAudiogram)}
          >
            {t("actions.new")}
          </button>
        ) : null}
      </div>
      <div className="print:hidden" {...testIdProps(testIds.audiology.list)}>
        {list.data?.items.length ? (
          <ul className="flex flex-wrap gap-2">
            {list.data.items.map((exam) => (
              <li key={exam.publicId}>
                <button
                  type="button"
                  className="rounded-full border border-border px-3 py-1 text-sm"
                  onClick={() => onAudiogramChange(exam.publicId)}
                  {...testIdProps(audiogramRowTestId(exam.publicId))}
                >
                  {formatDate(exam.performedAt, locale)}
                  {exam.isBaseline ? ` · ${t("overlay.baseline")}` : ""}
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p {...testIdProps(testIds.audiology.empty)}>{t("state.empty")}</p>
        )}
      </div>
      {conflict ? (
        <div
          className="flex flex-wrap items-center gap-3 rounded-lg border border-destructive/40 bg-destructive/5 p-3 print:hidden"
          {...testIdProps(testIds.audiology.conflict)}
        >
          <p className="text-sm text-destructive">{t("conflict")}</p>
          <button
            type="button"
            className="rounded-full border border-border px-3 py-1 text-sm"
            onClick={() => window.location.reload()}
            {...testIdProps(testIds.audiology.reload)}
          >
            {t("actions.reload")}
          </button>
        </div>
      ) : null}
      <div className="flex flex-wrap gap-2 print:hidden">
        <button
          type="button"
          className={`rounded-full px-3 py-1 text-sm ${
            viewMode === "dashboard"
              ? "bg-primary/10 text-primary"
              : "border border-border text-muted-foreground"
          }`}
          onClick={() => setViewMode("dashboard")}
          {...testIdProps(testIds.audiology.viewDashboard)}
        >
          {t("dashboard.viewDashboard")}
        </button>
        <button
          type="button"
          className={`rounded-full px-3 py-1 text-sm ${
            viewMode === "entry"
              ? "bg-primary/10 text-primary"
              : "border border-border text-muted-foreground"
          }`}
          onClick={() => setViewMode("entry")}
          {...testIdProps(testIds.audiology.viewEntry)}
        >
          {t("dashboard.viewEntry")}
        </button>
      </div>
      {viewMode === "dashboard" ? (
        <AudiologyDashboard
          patientId={patientId}
          audiogram={selected ?? null}
          history={list.data?.items ?? []}
          overlayCandidates={overlayOptions}
          overlayIds={overlayIds}
          onToggleOverlay={(publicId) => {
            setOverlayIds((current) => {
              const next = new Set(current);
              if (next.has(publicId)) {
                next.delete(publicId);
              } else {
                next.add(publicId);
              }
              return next;
            });
          }}
        />
      ) : null}
      {viewMode === "entry" ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 print:hidden">
            <Field
              label={t("fields.performedAt")}
              testId={testIds.audiology.performedAt}
            >
              <input
                type="datetime-local"
                disabled={readOnly}
                value={draft.performedAt}
                onChange={(event) =>
                  setDraft({ ...draft, performedAt: event.target.value })
                }
              />
            </Field>
            <SelectField
              label={t("fields.transducer")}
              testId={testIds.audiology.transducer}
              value={draft.transducer}
              disabled={readOnly}
              options={TRANSDUCERS.map((value) => ({
                value,
                label: transducerLabel(t, value),
              }))}
              onChange={(transducer) =>
                setDraft({
                  ...draft,
                  transducer: transducer as AudiogramDraft["transducer"],
                })
              }
            />
            <SelectField
              label={t("fields.method")}
              testId={testIds.audiology.method}
              value={draft.method}
              disabled={readOnly}
              options={TEST_METHODS.map((value) => ({
                value,
                label: methodLabel(t, value),
              }))}
              onChange={(method) =>
                setDraft({
                  ...draft,
                  method: method as AudiogramDraft["method"],
                })
              }
            />
            <SelectField
              label={t("fields.reliability")}
              testId={testIds.audiology.reliability}
              value={draft.reliability}
              disabled={readOnly}
              options={RELIABILITY_VALUES.map((value) => ({
                value,
                label: reliabilityLabel(t, value),
              }))}
              onChange={(reliability) =>
                setDraft({
                  ...draft,
                  reliability: reliability as AudiogramDraft["reliability"],
                })
              }
            />
            <Field
              label={t("fields.equipment")}
              testId={testIds.audiology.equipment}
            >
              <input
                disabled={readOnly}
                value={draft.equipment}
                onChange={(event) =>
                  setDraft({ ...draft, equipment: event.target.value })
                }
              />
            </Field>
            <Field
              label={t("fields.calibrationDate")}
              testId={testIds.audiology.calibrationDate}
            >
              <input
                type="date"
                disabled={readOnly}
                value={draft.calibrationDate}
                onChange={(event) =>
                  setDraft({ ...draft, calibrationDate: event.target.value })
                }
              />
            </Field>
          </div>
          <label className="flex items-center gap-2 text-sm print:hidden">
            <input
              type="checkbox"
              disabled={readOnly}
              checked={draft.showExtendedHigh}
              onChange={(event) =>
                setDraft({ ...draft, showExtendedHigh: event.target.checked })
              }
              {...testIdProps(testIds.audiology.extendedFreqToggle)}
            />
            {t("fields.extendedHigh")}
          </label>
          <div className="flex flex-wrap gap-2 print:hidden">
            <span className="text-sm font-medium">{t("plotMode.title")}</span>
            <ModeButton
              active={draft.activeMode.ear === "right"}
              testId={testIds.audiology.activeEarRight}
              disabled={readOnly}
              onClick={() =>
                setDraft({
                  ...draft,
                  activeMode: { ...draft.activeMode, ear: "right" },
                })
              }
            >
              {t("plotMode.earRight")}
            </ModeButton>
            <ModeButton
              active={draft.activeMode.ear === "left"}
              testId={testIds.audiology.activeEarLeft}
              disabled={readOnly}
              onClick={() =>
                setDraft({
                  ...draft,
                  activeMode: { ...draft.activeMode, ear: "left" },
                })
              }
            >
              {t("plotMode.earLeft")}
            </ModeButton>
            <ModeButton
              active={draft.activeMode.conduction === "air"}
              testId={testIds.audiology.activeConductionAir}
              disabled={readOnly}
              onClick={() =>
                setDraft({
                  ...draft,
                  activeMode: { ...draft.activeMode, conduction: "air" },
                })
              }
            >
              {t("plotMode.air")}
            </ModeButton>
            <ModeButton
              active={draft.activeMode.conduction === "bone"}
              testId={testIds.audiology.activeConductionBone}
              disabled={readOnly}
              onClick={() =>
                setDraft({
                  ...draft,
                  activeMode: { ...draft.activeMode, conduction: "bone" },
                })
              }
            >
              {t("plotMode.bone")}
            </ModeButton>
            <ModeButton
              active={draft.activeMode.isMasked}
              testId={testIds.audiology.activeMaskedToggle}
              disabled={readOnly}
              onClick={() =>
                setDraft({
                  ...draft,
                  activeMode: toggleActiveMasked(draft.activeMode),
                })
              }
            >
              {t("plotMode.masked")}
            </ModeButton>
          </div>
          <ComparisonOverlay
            overlays={overlayCandidates.map((row) => ({
              publicId: row.publicId,
              performedAt: row.performedAt,
              isBaseline: row.isBaseline,
              thresholds: row.thresholds,
            }))}
            selectedIds={overlayIds}
            onToggle={(publicId) => {
              setOverlayIds((current) => {
                const next = new Set(current);
                if (next.has(publicId)) {
                  next.delete(publicId);
                } else {
                  next.add(publicId);
                }
                return next;
              });
            }}
          />
          <AudiogramChart
            frequencies={frequencies}
            points={currentPoints}
            overlays={overlays}
            readOnly={readOnly}
            activeEar={draft.activeMode.ear}
            activeConduction={draft.activeMode.conduction}
            activeMasked={draft.activeMode.isMasked}
            onPlot={(frequencyHz, levelDb) => {
              setDraft((current: AudiogramDraft) => ({
                ...current,
                focusFrequencyHz: frequencyHz,
                cells: applyPlotToCells(
                  current.cells,
                  current.activeMode,
                  frequencyHz,
                  levelDb,
                ),
              }));
            }}
          />
          <AudiogramGrid
            frequencies={frequencies}
            cells={draft.cells}
            activeMode={draft.activeMode}
            focusFrequencyHz={draft.focusFrequencyHz}
            readOnly={readOnly}
            showExtendedHigh={draft.showExtendedHigh}
            onCellsChange={(cells) =>
              setDraft((current: AudiogramDraft) => ({ ...current, cells }))
            }
            onActiveModeChange={(activeMode) =>
              setDraft((current: AudiogramDraft) => ({
                ...current,
                activeMode,
              }))
            }
            onFocusFrequencyChange={(focusFrequencyHz) =>
              setDraft((current: AudiogramDraft) => ({
                ...current,
                focusFrequencyHz,
              }))
            }
            onToggleEar={() =>
              setDraft((current: AudiogramDraft) => ({
                ...current,
                activeMode: cycleActiveEar(current.activeMode),
              }))
            }
            onToggleMasked={() =>
              setDraft((current: AudiogramDraft) => ({
                ...current,
                activeMode: toggleActiveMasked(current.activeMode),
              }))
            }
          />
          <ServerMetricsPanel draft={draft} />
          {canInterpret ? (
            <>
              <label className="block space-y-1 text-sm print:hidden">
                {t("fields.interpretation")}
                <textarea
                  className="min-h-24 w-full rounded-lg border border-input bg-card px-3 py-2 text-sm"
                  disabled={readOnly}
                  value={draft.interpretationText}
                  onChange={(event) =>
                    setDraft({
                      ...draft,
                      interpretationText: event.target.value,
                    })
                  }
                  {...testIdProps(testIds.audiology.interpretation)}
                />
              </label>
              <label className="flex items-center gap-2 text-sm print:hidden">
                <input
                  type="checkbox"
                  disabled={readOnly}
                  checked={draft.isBaseline}
                  onChange={(event) =>
                    setDraft({ ...draft, isBaseline: event.target.checked })
                  }
                  {...testIdProps(testIds.audiology.isBaseline)}
                />
                {t("fields.isBaseline")}
              </label>
            </>
          ) : null}
          {issues.length > 0 ? (
            <ul {...testIdProps(testIds.audiology.validation)}>
              {issues.map((issue) => (
                <li key={issue}>
                  {t(`validation.${issue}` as "validation.performedAt")}
                </li>
              ))}
            </ul>
          ) : null}
          <div className="flex flex-wrap gap-2 print:hidden">
            {canEnter ? (
              <button
                type="button"
                className="rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
                disabled={readOnly || save.isPending}
                onClick={() => void persist(false)}
                {...testIdProps(testIds.audiology.save)}
              >
                {save.isPending ? t("actions.saving") : t("actions.save")}
              </button>
            ) : null}
            {canEnter ? (
              <button
                type="button"
                className="rounded-full border border-border px-4 py-2 text-sm font-medium disabled:opacity-50"
                disabled={readOnly || !draft.publicId || finalize.isPending}
                onClick={() => setConfirmFinalize(true)}
                {...testIdProps(testIds.audiology.finalize)}
              >
                {t("actions.finalize")}
              </button>
            ) : null}
            <button
              type="button"
              className="rounded-full border border-border px-4 py-2 text-sm font-medium"
              onClick={() => window.print()}
              {...testIdProps(testIds.audiology.print)}
            >
              {t("actions.print")}
            </button>
          </div>
        </>
      ) : null}
      {confirmFinalize ? (
        <div className="flex gap-2 print:hidden">
          <button
            type="button"
            className="rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground"
            onClick={() => {
              if (draft.publicId && draft.version) {
                void finalize
                  .mutateAsync({
                    audiogramId: draft.publicId,
                    body: { version: draft.version },
                  })
                  .then((saved) => {
                    setDraft((current: AudiogramDraft) => ({
                      ...current,
                      status: "final",
                      version: saved.version,
                      metrics: metricsFromRead(saved),
                    }));
                    setConfirmFinalize(false);
                  });
              }
            }}
            {...testIdProps(testIds.audiology.confirmFinalize)}
          >
            {t("actions.confirmFinalize")}
          </button>
          <button
            type="button"
            className="rounded-full border border-border px-4 py-2 text-sm"
            onClick={() => setConfirmFinalize(false)}
            {...testIdProps(testIds.audiology.cancelFinalize)}
          >
            {t("actions.cancelFinalize")}
          </button>
        </div>
      ) : null}
      <div
        className="audiogram-print-sheet hidden space-y-4 bg-white p-6 text-sm print:block"
        {...testIdProps(testIds.audiology.printSheet)}
      >
        <h1 className="text-lg font-semibold">{t("print.title")}</h1>
        <p>
          {t("print.patient")}: {patientName}
        </p>
        <p>
          {t("print.performed", {
            date: formatDate(draft.performedAt, locale),
          })}
        </p>
        <p>
          {t("print.reliability", {
            value: reliabilityLabel(t, draft.reliability),
          })}
        </p>
        <AudiogramChart
          frequencies={frequencies}
          points={currentPoints}
          overlays={overlays}
          readOnly
          activeEar={draft.activeMode.ear}
          activeConduction={draft.activeMode.conduction}
          activeMasked={draft.activeMode.isMasked}
          onPlot={() => undefined}
        />
        <p className="text-xs">{t("print.symbols")}</p>
        {draft.metrics.ptaRight !== null ? (
          <p>
            {t("metrics.pta", {
              ear: earLabel(t, "right"),
              value: draft.metrics.ptaRight,
              formula: ptaFormulaLabel(t, draft.metrics.ptaFormula),
            })}
          </p>
        ) : null}
        {draft.metrics.ptaLeft !== null ? (
          <p>
            {t("metrics.pta", {
              ear: earLabel(t, "left"),
              value: draft.metrics.ptaLeft,
              formula: ptaFormulaLabel(t, draft.metrics.ptaFormula),
            })}
          </p>
        ) : null}
        {draft.interpretationText ? (
          <p>
            {t("print.interpretation")}: {draft.interpretationText}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function ServerMetricsPanel({ draft }: { draft: AudiogramDraft }) {
  const t = useTranslations("audiology");
  const m = draft.metrics;
  return (
    <section
      className="space-y-1 rounded-xl border border-border bg-muted/20 p-4 text-sm print:hidden"
      {...testIdProps(testIds.audiology.serverMetrics)}
    >
      <h3 className="font-semibold">{t("metrics.title")}</h3>
      {m.ptaRight !== null ? (
        <p>
          {t("metrics.pta", {
            ear: earLabel(t, "right"),
            value: m.ptaRight,
            formula: ptaFormulaLabel(t, m.ptaFormula),
          })}
        </p>
      ) : null}
      {m.ptaLeft !== null ? (
        <p>
          {t("metrics.pta", {
            ear: earLabel(t, "left"),
            value: m.ptaLeft,
            formula: ptaFormulaLabel(t, m.ptaFormula),
          })}
        </p>
      ) : null}
      {m.asymmetryFlag ? <p>{t("metrics.asymmetry")}</p> : null}
      {m.shiftFlag ? <p>{t("metrics.shift")}</p> : null}
    </section>
  );
}

function ModeButton({
  active,
  testId,
  disabled,
  onClick,
  children,
}: {
  active: boolean;
  testId: string;
  disabled: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      className={`rounded-full px-3 py-1 text-sm ${
        active
          ? "bg-primary/10 text-primary"
          : "border border-border text-muted-foreground"
      }`}
      onClick={onClick}
      {...testIdProps(testId)}
    >
      {children}
    </button>
  );
}

function Field({
  label,
  testId,
  children,
}: {
  label: string;
  testId: string;
  children: ReactElement<InputHTMLAttributes<HTMLInputElement>>;
}) {
  return (
    <label className="space-y-1 text-sm">
      {label}
      {cloneElement(children, {
        className:
          "flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm",
        ...testIdProps(testId),
      })}
    </label>
  );
}

function SelectField({
  label,
  testId,
  value,
  disabled,
  options,
  onChange,
}: {
  label: string;
  testId: string;
  value: string;
  disabled: boolean;
  options: readonly { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="space-y-1 text-sm">
      {label}
      <select
        className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
        disabled={disabled}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        {...testIdProps(testId)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function localNow(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  const hour = String(now.getHours()).padStart(2, "0");
  const minute = String(now.getMinutes()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}T${hour}:${minute}`;
}
