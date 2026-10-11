"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";

import { OfficeProcedureFields } from "./OfficeProcedureFields";
import {
  usePatientOfficeProcedures,
  useSaveOfficeProcedure,
  useSignOfficeProcedure,
} from "../hooks/use-office-procedures";
import { isoToDateTimeLocal, localNow } from "../lib/clock";
import {
  SUBTYPES,
  draftFromRead,
  draftIssues,
  emptyDraft,
  toWrite,
  type ContentLocale,
  type OfficeDraft,
  type OfficeSubtype,
} from "../lib/draft";
import { optionLabel, recordStatusLabel } from "../lib/labels";
import { useCurrentClinicQuery } from "@/features/clinics";
import { formatDate } from "@/lib/i18n/format";
import {
  officeProcedureTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

const selectClass =
  "flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm";

type OfficeProcedureWorkspaceProps = {
  patientId: string;
  procedureId: string | null;
  onProcedureChange: (procedureId: string | null) => void;
};

export function OfficeProcedureWorkspace({
  patientId,
  procedureId,
  onProcedureChange,
}: OfficeProcedureWorkspaceProps) {
  const t = useTranslations("officeProcedures");
  const locale = useLocale();
  const contentLocale: ContentLocale =
    locale === "fr" || locale === "ar" ? locale : "en";
  const clinic = useCurrentClinicQuery();
  const timeZone = clinic.data?.timezone ?? "UTC";
  const listed = usePatientOfficeProcedures(patientId);
  const save = useSaveOfficeProcedure(patientId);
  const sign = useSignOfficeProcedure(patientId);
  const [draft, setDraft] = useState<OfficeDraft>(() => emptyDraft(localNow()));
  const [baseline, setBaseline] = useState<string | null>(null);
  const [issues, setIssues] = useState<string[]>([]);
  const [confirmingSign, setConfirmingSign] = useState(false);
  const loadedKey = useRef<string | null>(null);
  const selected = listed.data?.items.find(
    (row) => row.publicId === procedureId,
  );
  const readOnly = draft.procedureStatus !== "draft";
  const dirty = baseline !== null && JSON.stringify(draft) !== baseline;

  useEffect(() => {
    if (clinic.isLoading) {
      return;
    }
    const key = selected
      ? `${selected.publicId}:${selected.version}:${timeZone}`
      : procedureId
        ? "pending"
        : `new:${timeZone}`;
    if (loadedKey.current === key) {
      return;
    }
    loadedKey.current = key;
    if (!selected) {
      if (procedureId) {
        return;
      }
      const next = emptyDraft(localNow());
      setDraft(next);
      setBaseline(JSON.stringify(next));
      setIssues([]);
      return;
    }
    const next = draftFromRead(
      selected,
      isoToDateTimeLocal(selected.performedAt, timeZone),
    );
    setDraft(next);
    setBaseline(JSON.stringify(next));
    setIssues([]);
  }, [clinic.isLoading, procedureId, selected, timeZone]);

  async function persist(silent: boolean) {
    const found = draftIssues(draft, contentLocale);
    setIssues(found);
    const body = toWrite(draft, patientId, contentLocale, timeZone);
    if (!body || found.length > 0) {
      return null;
    }
    const saved = await save.mutateAsync({
      procedureId: draft.publicId,
      createBody: body,
      updateBody: { ...body, version: draft.version ?? 1 },
      silent,
    });
    onProcedureChange(saved.publicId);
    loadedKey.current = null;
    return saved;
  }

  if (listed.isLoading) {
    return (
      <p {...testIdProps(testIds.officeProcedures.loading)}>
        {t("state.loading")}
      </p>
    );
  }
  if (listed.isError) {
    return (
      <p {...testIdProps(testIds.officeProcedures.error)}>{t("state.error")}</p>
    );
  }

  return (
    <div className="space-y-6" {...testIdProps(testIds.officeProcedures.root)}>
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">{t("page.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("page.description")}</p>
      </header>
      <div
        className="flex flex-wrap gap-2"
        {...testIdProps(testIds.officeProcedures.list)}
      >
        <button
          type="button"
          className="rounded-full border border-border px-3 py-1.5 text-sm"
          onClick={() => {
            loadedKey.current = null;
            onProcedureChange(null);
          }}
          {...testIdProps(testIds.officeProcedures.newProcedure)}
        >
          {t("actions.newProcedure")}
        </button>
        {(listed.data?.items ?? []).length === 0 ? (
          <p {...testIdProps(testIds.officeProcedures.empty)}>{t("empty")}</p>
        ) : null}
        {(listed.data?.items ?? []).map((row) => (
          <button
            key={row.publicId}
            type="button"
            className="rounded-full border border-border px-3 py-1.5 text-sm"
            onClick={() => onProcedureChange(row.publicId)}
            {...testIdProps(officeProcedureTestId(row.publicId))}
          >
            {optionLabel(t, "subtype", row.detail.subtype)}{" "}
            {recordStatusLabel(t, row.procedureStatus)}
          </button>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]">
        <div className="space-y-4 rounded-xl border border-border bg-card p-4">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-1 text-sm md:col-span-2">
              {t("fields.subtype")}
              <select
                className={selectClass}
                disabled={readOnly || draft.publicId !== null}
                value={draft.subtype}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    subtype: event.target.value as OfficeSubtype,
                  })
                }
                {...testIdProps(testIds.officeProcedures.subtype)}
              >
                {SUBTYPES.map((subtype) => (
                  <option key={subtype} value={subtype}>
                    {optionLabel(t, "subtype", subtype)}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              {t("fields.performedAt")}
              <input
                className={selectClass}
                type="datetime-local"
                disabled={readOnly}
                value={draft.performedAt}
                onChange={(event) =>
                  setDraft({ ...draft, performedAt: event.target.value })
                }
                {...testIdProps(testIds.officeProcedures.performedAt)}
              />
            </label>
            <label className="space-y-1 text-sm">
              {t("fields.laterality")}
              <select
                className={selectClass}
                disabled={readOnly}
                value={draft.laterality}
                onChange={(event) =>
                  setDraft({ ...draft, laterality: event.target.value })
                }
                {...testIdProps(testIds.officeProcedures.laterality)}
              >
                {["right", "left", "bilateral", "midline", "na"].map(
                  (value) => (
                    <option key={value} value={value}>
                      {optionLabel(t, "laterality", value)}
                    </option>
                  ),
                )}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              {t("fields.anesthesia")}
              <select
                className={selectClass}
                disabled={readOnly}
                value={draft.anesthesia}
                onChange={(event) =>
                  setDraft({ ...draft, anesthesia: event.target.value })
                }
                {...testIdProps(testIds.officeProcedures.anesthesia)}
              >
                {["none", "topical_spray", "local_infiltration", "general"].map(
                  (value) => (
                    <option key={value} value={value}>
                      {optionLabel(t, "anesthesia", value)}
                    </option>
                  ),
                )}
              </select>
            </label>
          </div>
          <OfficeProcedureFields
            draft={draft}
            readOnly={readOnly}
            onChange={setDraft}
          />
          {issues.length > 0 ? (
            <p
              className="text-sm text-destructive"
              {...testIdProps(testIds.officeProcedures.validation)}
            >
              {t("validation.summary")}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-2 print:hidden">
            <button
              type="button"
              className="rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground"
              disabled={readOnly || save.isPending}
              onClick={() => void persist(false)}
              {...testIdProps(testIds.officeProcedures.save)}
            >
              {t("actions.save")}
            </button>
            <button
              type="button"
              className="rounded-full border border-border px-4 py-2 text-sm"
              disabled={readOnly || !draft.publicId || sign.isPending}
              onClick={() => setConfirmingSign(true)}
              {...testIdProps(testIds.officeProcedures.sign)}
            >
              {t("actions.sign")}
            </button>
          </div>
          {confirmingSign ? (
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground"
                disabled={sign.isPending}
                onClick={() => {
                  void (async () => {
                    const saved = dirty ? await persist(true) : selected;
                    if (!saved) {
                      return;
                    }
                    await sign.mutateAsync(saved.procedureId);
                    setConfirmingSign(false);
                    loadedKey.current = null;
                  })();
                }}
                {...testIdProps(testIds.officeProcedures.confirmSign)}
              >
                {t("actions.confirmSign")}
              </button>
              <button
                type="button"
                className="rounded-full border border-border px-4 py-2 text-sm"
                onClick={() => setConfirmingSign(false)}
                {...testIdProps(testIds.officeProcedures.cancelSign)}
              >
                {t("actions.cancelSign")}
              </button>
            </div>
          ) : null}
        </div>
        <ProcedureReport draft={draft} locale={locale} />
      </div>
    </div>
  );
}

function ProcedureReport({
  draft,
  locale,
}: {
  draft: OfficeDraft;
  locale: string;
}) {
  const t = useTranslations("officeProcedures");
  const removal =
    draft.subtype === "epistaxis_management" &&
    ["anterior_pack", "posterior_pack", "balloon"].includes(
      draft.epistaxisMethod,
    )
      ? draft.packRemovalDate
      : draft.subtype === "nasal_fracture_reduction"
        ? draft.splintRemovalDate
        : "";
  const result =
    draft.subtype === "fine_needle_aspiration" ||
    draft.subtype === "oral_pharyngeal_biopsy"
      ? draft.resultDueDate
      : "";
  const followUp = draft.subtype === "sialendoscopy" ? draft.followUpDate : "";
  return (
    <aside
      className="space-y-3 rounded-xl border border-border bg-card p-4"
      {...testIdProps(testIds.officeProcedures.report)}
    >
      <h2 className="text-sm font-semibold">{t("report.title")}</h2>
      <p>{optionLabel(t, "subtype", draft.subtype)}</p>
      <p>
        {optionLabel(t, "laterality", draft.laterality)} ·{" "}
        {recordStatusLabel(t, draft.procedureStatus)}
      </p>
      {removal ? (
        <p>
          {t("report.removalDue")}{" "}
          <span className="num">
            {formatDate(`${removal}T12:00:00`, locale)}
          </span>
        </p>
      ) : null}
      {result ? (
        <p>
          {t("report.resultDue")}{" "}
          <span className="num">
            {formatDate(`${result}T12:00:00`, locale)}
          </span>
        </p>
      ) : null}
      {followUp ? (
        <p>
          {t("report.followUp")}{" "}
          <span className="num">
            {formatDate(`${followUp}T12:00:00`, locale)}
          </span>
        </p>
      ) : null}
    </aside>
  );
}
