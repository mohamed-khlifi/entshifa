"use client";

import { useTranslations } from "next-intl";

import { optionLabel } from "../lib/labels";
import type { OfficeDraft } from "../lib/draft";
import { testIdProps, testIds } from "@/lib/test/test-id";

const selectClass =
  "flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm";

const MUSCLES: Record<string, readonly string[]> = {
  spasmodic_dysphonia: ["thyroarytenoid", "lateral_cricoarytenoid"],
  sialorrhea: ["parotid", "submandibular"],
  cricopharyngeal: ["cricopharyngeus"],
};

const FINDINGS = ["stone", "stenosis", "mucus_plug"] as const;

type OfficeProcedureFieldsProps = {
  draft: OfficeDraft;
  readOnly: boolean;
  onChange: (draft: OfficeDraft) => void;
};

export function OfficeProcedureFields({
  draft,
  readOnly,
  onChange,
}: OfficeProcedureFieldsProps) {
  const t = useTranslations("officeProcedures");
  const set = (patch: Partial<OfficeDraft>) => onChange({ ...draft, ...patch });

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {draft.subtype === "epistaxis_management" ? (
        <EpistaxisFields draft={draft} readOnly={readOnly} onChange={set} />
      ) : null}
      {draft.subtype === "fine_needle_aspiration" ? (
        <AspirationFields draft={draft} readOnly={readOnly} onChange={set} />
      ) : null}
      {draft.subtype === "oral_pharyngeal_biopsy" ? (
        <BiopsyFields draft={draft} readOnly={readOnly} onChange={set} />
      ) : null}
      {draft.subtype === "botulinum_injection" ? (
        <BotulinumFields draft={draft} readOnly={readOnly} onChange={set} />
      ) : null}
      {draft.subtype === "peritonsillar_drainage" ? (
        <>
          <Choice
            label={t("fields.method")}
            value={draft.drainageMethod}
            options={["aspiration", "incision"]}
            group="drainage"
            testId={testIds.officeProcedures.method}
            disabled={readOnly}
            onChange={(drainageMethod) => set({ drainageMethod })}
          />
          <Text
            label={t("fields.volume")}
            value={draft.volumeMl}
            disabled={readOnly}
            suffix="mL"
            onChange={(volumeMl) => set({ volumeMl })}
          />
          <YesNo
            label={t("fields.cultureSent")}
            value={draft.cultureSent}
            disabled={readOnly}
            onChange={(cultureSent) => set({ cultureSent })}
          />
        </>
      ) : null}
      {draft.subtype === "nasal_fracture_reduction" ? (
        <>
          <Choice
            label={t("fields.splintType")}
            value={draft.splintType}
            options={["thermoplastic", "plaster", "denver", "tape"]}
            group="splint"
            testId={testIds.officeProcedures.splintType}
            disabled={readOnly}
            onChange={(splintType) => set({ splintType })}
          />
          <Text
            label={t("fields.splintRemoval")}
            value={draft.splintRemovalDate}
            type="date"
            disabled={readOnly}
            testId={testIds.officeProcedures.splintRemoval}
            onChange={(splintRemovalDate) => set({ splintRemovalDate })}
          />
        </>
      ) : null}
      {draft.subtype === "sialendoscopy" ? (
        <>
          <Choice
            label={t("fields.gland")}
            value={draft.gland}
            options={["parotid", "submandibular"]}
            group="gland"
            disabled={readOnly}
            onChange={(gland) => set({ gland })}
          />
          <fieldset className="space-y-2 text-sm md:col-span-2">
            <legend>{t("fields.findings")}</legend>
            <div className="flex flex-wrap gap-3">
              {FINDINGS.map((finding) => (
                <label key={finding} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    disabled={readOnly}
                    checked={draft.findings.includes(finding)}
                    onChange={(event) => {
                      const findings = event.target.checked
                        ? [...draft.findings, finding]
                        : draft.findings.filter((item) => item !== finding);
                      set({
                        findings,
                        stoneRemoved:
                          finding === "stone" && !event.target.checked
                            ? false
                            : draft.stoneRemoved,
                      });
                    }}
                  />
                  {optionLabel(t, "finding", finding)}
                </label>
              ))}
            </div>
          </fieldset>
          <YesNo
            label={t("fields.stoneRemoved")}
            value={draft.stoneRemoved}
            disabled={readOnly || !draft.findings.includes("stone")}
            onChange={(stoneRemoved) => set({ stoneRemoved })}
          />
          <Text
            label={t("fields.followUp")}
            value={draft.followUpDate}
            type="date"
            disabled={readOnly}
            testId={testIds.officeProcedures.followUp}
            onChange={(followUpDate) => set({ followUpDate })}
          />
        </>
      ) : null}
      {draft.subtype === "epistaxis_management" ? null : (
        <label className="space-y-1 text-sm md:col-span-2">
          {t("fields.note")}
          <textarea
            className="min-h-20 w-full rounded-lg border border-input bg-card px-2 py-2 text-sm"
            disabled={readOnly}
            value={draft.noteText}
            onChange={(event) => set({ noteText: event.target.value })}
            {...testIdProps(testIds.officeProcedures.note)}
          />
        </label>
      )}
    </div>
  );
}

function EpistaxisFields({
  draft,
  readOnly,
  onChange,
}: {
  draft: OfficeDraft;
  readOnly: boolean;
  onChange: (patch: Partial<OfficeDraft>) => void;
}) {
  const t = useTranslations("officeProcedures");
  const packed = ["anterior_pack", "posterior_pack", "balloon"].includes(
    draft.epistaxisMethod,
  );
  return (
    <>
      <YesNo
        label={t("fields.siteFound")}
        value={draft.siteFound}
        disabled={readOnly}
        testId={testIds.officeProcedures.siteFound}
        onChange={(siteFound) => onChange({ siteFound })}
      />
      {draft.siteFound ? (
        <Choice
          label={t("fields.siteFound")}
          value={draft.bleedingSite}
          options={[
            "little_area",
            "septum",
            "inferior_turbinate",
            "nasal_floor",
            "nasopharynx",
          ]}
          group="bleedingSite"
          testId={testIds.officeProcedures.bleedingSite}
          disabled={readOnly}
          onChange={(bleedingSite) => onChange({ bleedingSite })}
        />
      ) : null}
      <Choice
        label={t("fields.method")}
        value={draft.epistaxisMethod}
        options={[
          "silver_nitrate",
          "electrocautery",
          "anterior_pack",
          "posterior_pack",
          "balloon",
        ]}
        group="method"
        testId={testIds.officeProcedures.method}
        disabled={readOnly}
        onChange={(epistaxisMethod) => onChange({ epistaxisMethod })}
      />
      {draft.epistaxisMethod === "anterior_pack" ? (
        <Choice
          label={t("fields.packType")}
          value={draft.packType}
          options={["merocel", "rapid_rhino", "ribbon_gauze"]}
          group="packType"
          testId={testIds.officeProcedures.packType}
          disabled={readOnly}
          onChange={(packType) => onChange({ packType })}
        />
      ) : null}
      {packed ? (
        <Text
          label={t("fields.packRemoval")}
          value={draft.packRemovalDate}
          type="date"
          disabled={readOnly}
          testId={testIds.officeProcedures.packRemoval}
          onChange={(packRemovalDate) => onChange({ packRemovalDate })}
        />
      ) : null}
      <Text
        label={t("fields.systolic")}
        value={draft.systolic}
        disabled={readOnly}
        suffix="mmHg"
        testId={testIds.officeProcedures.systolic}
        onChange={(systolic) => onChange({ systolic })}
      />
      <Text
        label={t("fields.diastolic")}
        value={draft.diastolic}
        disabled={readOnly}
        suffix="mmHg"
        testId={testIds.officeProcedures.diastolic}
        onChange={(diastolic) => onChange({ diastolic })}
      />
      <Choice
        label={t("fields.anticoagulant")}
        value={draft.anticoagulant}
        options={["yes", "no", "unknown"]}
        group="anticoagulant"
        testId={testIds.officeProcedures.anticoagulant}
        disabled={readOnly}
        onChange={(anticoagulant) => onChange({ anticoagulant })}
      />
      <label className="space-y-1 text-sm md:col-span-2">
        {t("fields.advice")}
        <textarea
          className="min-h-20 w-full rounded-lg border border-input bg-card px-2 py-2 text-sm"
          disabled={readOnly}
          value={draft.adviceText}
          onChange={(event) => onChange({ adviceText: event.target.value })}
          {...testIdProps(testIds.officeProcedures.advice)}
        />
      </label>
    </>
  );
}

function AspirationFields({
  draft,
  readOnly,
  onChange,
}: {
  draft: OfficeDraft;
  readOnly: boolean;
  onChange: (patch: Partial<OfficeDraft>) => void;
}) {
  const t = useTranslations("officeProcedures");
  return (
    <>
      <Choice
        label={t("fields.fnaSite")}
        value={draft.fnaSite}
        options={["thyroid", "parotid", "submandibular", "neck_node", "other"]}
        group="fnaSite"
        disabled={readOnly}
        onChange={(fnaSite) => onChange({ fnaSite })}
      />
      {draft.fnaSite === "other" ? (
        <Text
          label={t("fields.siteNote")}
          value={draft.fnaSiteNote}
          disabled={readOnly}
          onChange={(fnaSiteNote) => onChange({ fnaSiteNote })}
        />
      ) : null}
      <Text
        label={t("fields.needleGauge")}
        value={draft.needleGauge}
        disabled={readOnly}
        onChange={(needleGauge) => onChange({ needleGauge })}
      />
      <Text
        label={t("fields.passes")}
        value={draft.passes}
        disabled={readOnly}
        onChange={(passes) => onChange({ passes })}
      />
      <YesNo
        label={t("fields.ultrasound")}
        value={draft.ultrasoundGuided}
        disabled={readOnly}
        onChange={(ultrasoundGuided) => onChange({ ultrasoundGuided })}
      />
      <Text
        label={t("fields.laboratory")}
        value={draft.laboratoryText}
        disabled={readOnly}
        testId={testIds.officeProcedures.laboratory}
        onChange={(laboratoryText) => onChange({ laboratoryText })}
      />
      <Text
        label={t("fields.resultDue")}
        value={draft.resultDueDate}
        type="date"
        disabled={readOnly}
        testId={testIds.officeProcedures.resultDue}
        onChange={(resultDueDate) => onChange({ resultDueDate })}
      />
    </>
  );
}

function BiopsyFields({
  draft,
  readOnly,
  onChange,
}: {
  draft: OfficeDraft;
  readOnly: boolean;
  onChange: (patch: Partial<OfficeDraft>) => void;
}) {
  const t = useTranslations("officeProcedures");
  return (
    <>
      <Choice
        label={t("fields.biopsySite")}
        value={draft.biopsySite}
        options={[
          "oral_cavity",
          "tongue",
          "palate",
          "tonsil",
          "oropharynx",
          "hypopharynx",
        ]}
        group="biopsySite"
        disabled={readOnly}
        onChange={(biopsySite) => onChange({ biopsySite })}
      />
      <Choice
        label={t("fields.technique")}
        value={draft.technique}
        options={["punch", "incisional", "excisional"]}
        group="technique"
        disabled={readOnly}
        onChange={(technique) => onChange({ technique })}
      />
      <Text
        label={t("fields.laboratory")}
        value={draft.laboratoryText}
        disabled={readOnly}
        testId={testIds.officeProcedures.laboratory}
        onChange={(laboratoryText) => onChange({ laboratoryText })}
      />
      <Text
        label={t("fields.resultDue")}
        value={draft.resultDueDate}
        type="date"
        disabled={readOnly}
        testId={testIds.officeProcedures.resultDue}
        onChange={(resultDueDate) => onChange({ resultDueDate })}
      />
    </>
  );
}

function BotulinumFields({
  draft,
  readOnly,
  onChange,
}: {
  draft: OfficeDraft;
  readOnly: boolean;
  onChange: (patch: Partial<OfficeDraft>) => void;
}) {
  const t = useTranslations("officeProcedures");
  const muscles = MUSCLES[draft.indication] ?? [];
  return (
    <>
      <Choice
        label={t("fields.indication")}
        value={draft.indication}
        options={["spasmodic_dysphonia", "sialorrhea", "cricopharyngeal"]}
        group="indication"
        disabled={readOnly}
        onChange={(indication) =>
          onChange({
            indication,
            injections: [
              {
                muscle: MUSCLES[indication]?.[0] ?? "",
                side: "right",
                doseUnits: "",
              },
            ],
          })
        }
      />
      {draft.injections.map((injection, index) => (
        <div key={index} className="grid gap-4 md:col-span-2 md:grid-cols-3">
          <Choice
            label={t("fields.muscle")}
            value={injection.muscle}
            options={muscles}
            group="muscle"
            disabled={readOnly}
            onChange={(muscle) => {
              const injections = draft.injections.map((item, itemIndex) =>
                itemIndex === index ? { ...item, muscle } : item,
              );
              onChange({ injections });
            }}
          />
          <Choice
            label={t("fields.laterality")}
            value={injection.side}
            options={["right", "left", "bilateral", "midline"]}
            group="injectionSide"
            disabled={readOnly}
            onChange={(side) => {
              const injections = draft.injections.map((item, itemIndex) =>
                itemIndex === index ? { ...item, side } : item,
              );
              onChange({ injections });
            }}
          />
          <Text
            label={t("fields.dose")}
            value={injection.doseUnits}
            disabled={readOnly}
            suffix="U"
            onChange={(doseUnits) => {
              const injections = draft.injections.map((item, itemIndex) =>
                itemIndex === index ? { ...item, doseUnits } : item,
              );
              onChange({ injections });
            }}
          />
        </div>
      ))}
    </>
  );
}

function Choice({
  label,
  value,
  options,
  group,
  disabled,
  testId,
  onChange,
}: {
  label: string;
  value: string;
  options: readonly string[];
  group: string;
  disabled: boolean;
  testId?: string;
  onChange: (value: string) => void;
}) {
  const t = useTranslations("officeProcedures");
  return (
    <label className="space-y-1 text-sm">
      {label}
      <select
        className={selectClass}
        disabled={disabled}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        {...(testId ? testIdProps(testId) : {})}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {optionLabel(t, group, option)}
          </option>
        ))}
      </select>
    </label>
  );
}

function Text({
  label,
  value,
  disabled,
  onChange,
  type = "text",
  suffix,
  testId,
}: {
  label: string;
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  type?: "text" | "date";
  suffix?: string;
  testId?: string;
}) {
  return (
    <label className="space-y-1 text-sm">
      {label}
      <span className="flex items-center gap-2">
        <input
          className={selectClass}
          type={type}
          disabled={disabled}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          {...(testId ? testIdProps(testId) : {})}
        />
        {suffix ? (
          <span className="text-sm text-muted-foreground">{suffix}</span>
        ) : null}
      </span>
    </label>
  );
}

function YesNo({
  label,
  value,
  disabled,
  onChange,
  testId,
}: {
  label: string;
  value: boolean;
  disabled: boolean;
  onChange: (value: boolean) => void;
  testId?: string;
}) {
  const t = useTranslations("officeProcedures");
  return (
    <label className="space-y-1 text-sm">
      {label}
      <select
        className={selectClass}
        disabled={disabled}
        value={value ? "yes" : "no"}
        onChange={(event) => onChange(event.target.value === "yes")}
        {...(testId ? testIdProps(testId) : {})}
      >
        <option value="yes">{t("values.yes")}</option>
        <option value="no">{t("values.no")}</option>
      </select>
    </label>
  );
}
