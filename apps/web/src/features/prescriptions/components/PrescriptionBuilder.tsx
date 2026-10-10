"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMemo, useRef, useState } from "react";
import { useFieldArray, useForm, useFormContext } from "react-hook-form";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { Form } from "@/components/forms/Form";
import { SelectField } from "@/components/forms/SelectField";
import { TextAreaField } from "@/components/forms/TextAreaField";
import { TextField } from "@/components/forms/TextField";
import { Button } from "@/components/ui/button";
import { useCurrentClinicQuery } from "@/features/clinics";
import { usePatientQuery } from "@/features/patients";
import type {
  CalculationRead,
  DrugRead,
  FormularyEntryRead,
  PrescriptionTemplateRead,
} from "@/lib/api/generated";
import { MEDICAL_UNITS } from "@/lib/i18n/format";
import { Permission } from "@/lib/permissions";
import {
  prescriptionTemplateTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";
import { usePermission } from "@/providers/permission-provider";

import { DrugSearch } from "./DrugSearch";
import { EntHelpers } from "./EntHelpers";
import { PrescriptionPaper } from "./PrescriptionPaper";
import { SafetyAlerts } from "./SafetyAlerts";
import type { PrescriptionRoute } from "../constants";
import {
  useCalculateDoseMutation,
  useCancelPrescriptionMutation,
  useCreatePrescriptionMutation,
  useCreateTemplateMutation,
  useDrugSearchQuery,
  useFormularyQuery,
  useGenerateTaperMutation,
  useIssuePrescriptionMutation,
  useLiveSafety,
  usePrescriptionTemplatesQuery,
  useUpdatePrescriptionMutation,
} from "../hooks/use-prescription-queries";
import {
  flagUnit,
  flagValue,
  paperLocale,
  scheduleDoses,
} from "../lib/display";
import { alertCopy, isRoute, routeLabel } from "../lib/labels";
import {
  appendInstruction,
  emptyItem,
  itemFromTemplate,
  itemWrite,
  readDefaultDuration,
  readIndicationCodes,
  readStoredTaper,
  type ItemValues,
  type PrescriptionFormValues,
} from "../lib/items";
import { lineFromDraft, paperShell } from "../lib/paper";
import { hasUnresolvedBlock, placeAlerts } from "../lib/safety";
import {
  catalogOnlyDrugs,
  templateTitle,
  templatesForVisit,
} from "../lib/search";
import {
  createPrescriptionFormSchema,
  createTemplateCodeSchema,
} from "../schemas/prescription.schema";

type PrescriptionBuilderProps = {
  patientId: string;
  encounterId: string;
  complaintConceptIds: readonly string[];
  showPaper?: boolean;
};

function routeForForm(form: string | undefined): PrescriptionRoute {
  switch (form) {
    case "spray":
      return "nasal";
    case "drops":
      return "otic";
    case "injection":
      return "injection";
    default:
      return "oral";
  }
}

export function PrescriptionBuilder({
  patientId,
  encounterId,
  complaintConceptIds,
  showPaper = true,
}: PrescriptionBuilderProps) {
  const t = useTranslations("prescriptions");
  const canSign = usePermission(Permission.PRESCRIPTION_SIGN);
  const patient = usePatientQuery(patientId);
  const clinic = useCurrentClinicQuery();
  const schema = useMemo(() => createPrescriptionFormSchema(t), [t]);
  const form = useForm<PrescriptionFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      isPediatric: false,
      weightKg: "",
      notes: "",
      items: [],
    },
  });
  const rows = useFieldArray({
    control: form.control,
    name: "items",
  });
  const [query, setQuery] = useState("");
  const [freeTextName, setFreeTextName] = useState("");
  const [selected, setSelected] = useState(0);
  const [templateCode, setTemplateCode] = useState("");
  const [rulesByKey, setRulesByKey] = useState<Record<string, unknown>>({});
  const [previews, setPreviews] = useState<Record<string, CalculationRead>>({});
  const [taperPreview, setTaperPreview] = useState<string[]>([]);
  const [taperByKey, setTaperByKey] = useState<Record<string, string[]>>({});
  const [saved, setSaved] = useState<{
    id: string;
    version: number;
    status: string;
  } | null>(null);
  const idempotencyKey = useRef(crypto.randomUUID());

  const formulary = useFormularyQuery(query);
  const drugs = useDrugSearchQuery(query);
  const templates = usePrescriptionTemplatesQuery();
  const createDraft = useCreatePrescriptionMutation(patientId);
  const updateDraft = useUpdatePrescriptionMutation(patientId);
  const issue = useIssuePrescriptionMutation(patientId);
  const cancel = useCancelPrescriptionMutation(patientId);
  const saveTemplate = useCreateTemplateMutation();
  const calculate = useCalculateDoseMutation(patientId);
  const taper = useGenerateTaperMutation(patientId);

  const draftItems = form.watch("items");
  const isPediatric = form.watch("isPediatric");
  const weightKg = form.watch("weightKg");
  const locked = saved?.status === "issued" || saved?.status === "cancelled";

  const prepared = useMemo(() => {
    const items = [];
    const keys: string[] = [];
    for (const item of draftItems) {
      const write = itemWrite(item, items.length);
      if (!write) {
        continue;
      }
      items.push(write);
      keys.push(item.key);
    }
    return {
      keys,
      request:
        items.length === 0
          ? null
          : {
              isPediatric,
              weightKg: weightKg.trim() || null,
              items,
            },
    };
  }, [draftItems, isPediatric, weightKg]);

  const alerts = useLiveSafety(patientId, prepared.request);
  const placed = placeAlerts(alerts, prepared.keys);
  const itemMap = new Map(draftItems.map((item) => [item.key, item]));
  const blocked = hasUnresolvedBlock(placed, itemMap);

  const rankedTemplates = templatesForVisit(
    templates.data?.items ?? [],
    complaintConceptIds,
    query,
  );
  const formularyItems = (formulary.data?.items ?? []).filter(
    (entry) => entry.isAvailable,
  );
  const catalog = catalogOnlyDrugs(drugs.data?.items ?? [], formularyItems);

  function addItem(item: ItemValues, rules?: unknown) {
    rows.append(item);
    setSelected(draftItems.length);
    if (rules !== undefined) {
      setRulesByKey((current) => ({ ...current, [item.key]: rules }));
    }
  }

  function pickFormulary(entry: FormularyEntryRead) {
    const item = emptyItem(crypto.randomUUID());
    item.formularyEntryPublicId = entry.publicId;
    item.label = entry.brandName;
    item.route = routeForForm(entry.drug.forms[0]?.form);
    item.durationDays =
      readDefaultDuration(entry.dosingRules) ?? item.durationDays;
    addItem(item, entry.dosingRules);
    setQuery("");
  }

  function pickCatalog(drug: DrugRead) {
    const item = emptyItem(crypto.randomUUID());
    const name = drug.concept?.display ?? drug.innName;
    item.freeTextName = name;
    item.label = name;
    addItem(item);
    setQuery("");
  }

  function applyTemplate(template: PrescriptionTemplateRead) {
    const next = template.items.flatMap((raw) => {
      const item = itemFromTemplate(raw, crypto.randomUUID());
      return item ? [item] : [];
    });
    form.setValue("isPediatric", template.isPediatric);
    form.setValue("items", next);
    setSelected(0);
    setTaperByKey({});
    setPreviews({});
  }

  async function persist(andIssue: boolean) {
    if (andIssue && blocked) {
      return;
    }
    const parsed = schema.safeParse(form.getValues());
    if (!parsed.success) {
      void form.handleSubmit(() => undefined)();
      return;
    }
    const items = parsed.data.items.flatMap((item, index) => {
      const write = itemWrite(item, index);
      return write ? [write] : [];
    });
    if (items.length !== parsed.data.items.length) {
      return;
    }
    const locale = paperLocale(
      patient.data?.preferredLocale,
      clinic.data?.defaultLocale,
    );
    const shared = {
      locale,
      isPediatric: parsed.data.isPediatric,
      weightKg: parsed.data.weightKg.trim() || null,
      notes: parsed.data.notes.trim() || null,
      items,
    };
    const record = saved
      ? await updateDraft.mutateAsync({
          prescriptionId: saved.id,
          body: { ...shared, version: saved.version },
        })
      : await createDraft.mutateAsync({
          body: { ...shared, encounterPublicId: encounterId },
          idempotencyKey: idempotencyKey.current,
        });
    const issued = andIssue ? await issue.mutateAsync(record.publicId) : record;
    setSaved({
      id: issued.publicId,
      version: issued.version,
      status: issued.status,
    });
    toast.success(andIssue ? t("builder.issued") : t("builder.saved"));
  }

  const locale = paperLocale(
    patient.data?.preferredLocale,
    clinic.data?.defaultLocale,
  );
  const model =
    patient.data && clinic.data
      ? paperShell(
          clinic.data,
          patient.data,
          locale,
          weightKg.trim() || null,
          saved?.id ?? null,
          draftItems.map((item) =>
            lineFromDraft(item, taperByKey[item.key] ?? []),
          ),
        )
      : null;

  return (
    <div className="space-y-4">
      <div
        className="space-y-4 print:hidden"
        {...testIdProps(testIds.prescriptions.builder)}
      >
        <h2 className="text-lg font-semibold">{t("builder.title")}</h2>
        <DrugSearch
          query={query}
          onQueryChange={setQuery}
          formulary={formularyItems}
          catalog={catalog}
          onPickFormulary={pickFormulary}
          onPickCatalog={pickCatalog}
        />
        <div
          className="space-y-2"
          {...testIdProps(testIds.prescriptions.templatesHeading)}
        >
          <h3 className="text-sm font-semibold">
            {t("builder.templatesHeading")}
          </h3>
          {rankedTemplates.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {t("templates.empty")}
            </p>
          ) : (
            <ul className="space-y-1">
              {rankedTemplates.map((template) => (
                <li key={template.publicId}>
                  <Button
                    type="button"
                    variant="secondary"
                    disabled={locked}
                    onClick={() => applyTemplate(template)}
                    {...testIdProps(
                      prescriptionTemplateTestId(template.publicId),
                    )}
                  >
                    {t("templates.apply")}: {templateTitle(template, null)}
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <Form form={form} onSubmit={() => persist(false)}>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={isPediatric}
              disabled={locked}
              onChange={(event) =>
                form.setValue("isPediatric", event.target.checked)
              }
              {...testIdProps(testIds.prescriptions.pediatric)}
            />
            {t("builder.pediatric")}
          </label>
          <TextField
            name="weightKg"
            label={t("builder.weight")}
            unit={MEDICAL_UNITS.kg}
            disabled={locked}
          />
          <div className="flex flex-wrap items-end gap-2">
            <label className="block flex-1 text-sm">
              {t("builder.freeTextName")}
              <input
                value={freeTextName}
                disabled={locked}
                onChange={(event) => setFreeTextName(event.target.value)}
                className="mt-1 flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
                {...testIdProps(testIds.prescriptions.freeTextName)}
              />
            </label>
            <Button
              type="button"
              variant="secondary"
              disabled={locked || freeTextName.trim().length === 0}
              onClick={() => {
                const item = emptyItem(crypto.randomUUID());
                item.freeTextName = freeTextName.trim();
                item.label = freeTextName.trim();
                addItem(item);
                setFreeTextName("");
              }}
              {...testIdProps(testIds.prescriptions.freeText)}
            >
              {t("builder.freeText")}
            </Button>
          </div>
          {rows.fields.map((field, index) => (
            <ItemRow
              key={field.id}
              index={index}
              locked={locked}
              selected={selected === index}
              onSelect={() => setSelected(index)}
              rules={rulesByKey[draftItems[index]?.key ?? ""] ?? null}
              preview={previews[draftItems[index]?.key ?? ""] ?? null}
              alerts={placed.filter(
                (alert) => alert.itemKey === draftItems[index]?.key,
              )}
              onRemove={() => rows.remove(index)}
              onCalculate={() => {
                const item = form.getValues(`items.${index}`);
                if (!item || weightKg.trim().length === 0) {
                  return;
                }
                void calculate
                  .mutateAsync({
                    formularyEntryPublicId: item.formularyEntryPublicId,
                    weightKg: weightKg.trim(),
                    indicationCode: item.indicationCode || null,
                  })
                  .then((result) => {
                    setPreviews((current) => ({
                      ...current,
                      [item.key]: result,
                    }));
                    form.setValue(
                      `items.${index}.calculateFromFormulary`,
                      true,
                    );
                  });
              }}
            />
          ))}
          <TextAreaField
            name="notes"
            label={t("builder.notes")}
            disabled={locked}
          />
          <SafetyAlerts
            alerts={placed}
            blocked={blocked && draftItems.length > 0}
          />
          <div className="flex flex-wrap gap-2">
            <Button
              type="submit"
              disabled={
                locked || createDraft.isPending || updateDraft.isPending
              }
              {...testIdProps(testIds.prescriptions.saveDraft)}
            >
              {t("builder.saveDraft")}
            </Button>
            {canSign ? (
              <Button
                type="button"
                disabled={locked || blocked || issue.isPending}
                onClick={() => void persist(true)}
                {...testIdProps(testIds.prescriptions.issue)}
              >
                {t("builder.issue")}
              </Button>
            ) : null}
            {canSign && saved && saved.status !== "cancelled" ? (
              <Button
                type="button"
                variant="secondary"
                disabled={cancel.isPending}
                onClick={() => {
                  void cancel.mutateAsync(saved.id).then((record) => {
                    setSaved({
                      id: record.publicId,
                      version: record.version,
                      status: record.status,
                    });
                    toast.success(t("builder.cancelled"));
                  });
                }}
                {...testIdProps(testIds.prescriptions.cancel)}
              >
                {t("builder.cancel")}
              </Button>
            ) : null}
            <Button
              type="button"
              variant="secondary"
              onClick={() => window.print()}
              {...testIdProps(testIds.prescriptions.print)}
            >
              {t("builder.print")}
            </Button>
          </div>
          <div className="flex flex-wrap items-end gap-2">
            <label className="block text-sm">
              {t("templates.code")}
              <input
                value={templateCode}
                onChange={(event) => setTemplateCode(event.target.value)}
                className="mt-1 flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
                {...testIdProps(testIds.prescriptions.templateCode)}
              />
            </label>
            <Button
              type="button"
              variant="secondary"
              disabled={saveTemplate.isPending}
              onClick={() => {
                const codeCheck = createTemplateCodeSchema(t).safeParse({
                  code: templateCode,
                });
                if (!codeCheck.success || prepared.request == null) {
                  return;
                }
                void saveTemplate
                  .mutateAsync({
                    code: codeCheck.data.code,
                    nameKey: `prescriptions.templates.${codeCheck.data.code}`,
                    isPediatric,
                    complaintConceptIds: [...complaintConceptIds],
                    items: prepared.request.items,
                  })
                  .then(() => {
                    setTemplateCode("");
                    toast.success(t("builder.templateSaved"));
                  });
              }}
              {...testIdProps(testIds.prescriptions.templateSave)}
            >
              {t("templates.save")}
            </Button>
          </div>
        </Form>
        <EntHelpers
          disabled={locked || draftItems.length === 0}
          schedule={taperPreview}
          onAppend={(text) => {
            const item = draftItems[selected];
            if (!item) {
              return;
            }
            form.setValue(
              `items.${selected}.instructionsText`,
              appendInstruction(item.instructionsText, text),
            );
          }}
          onPreviewTaper={(input) => {
            void taper.mutateAsync(input).then((result) => {
              setTaperPreview(scheduleDoses(result));
            });
          }}
          onApplyTaper={(input) => {
            const item = draftItems[selected];
            if (!item) {
              return;
            }
            form.setValue(`items.${selected}.useFormularyTaper`, false);
            form.setValue(`items.${selected}.taperStartMg`, input.startMg);
            form.setValue(`items.${selected}.taperStepMg`, input.stepMg);
            form.setValue(
              `items.${selected}.taperDaysPerStep`,
              input.daysPerStep,
            );
            form.setValue(`items.${selected}.taperMinimumMg`, input.minimumMg);
            setTaperByKey((current) => ({
              ...current,
              [item.key]: taperPreview,
            }));
          }}
        />
      </div>
      {showPaper && model ? (
        <PrescriptionPaper locale={locale} model={model} />
      ) : null}
    </div>
  );
}

function ItemRow({
  index,
  locked,
  selected,
  onSelect,
  rules,
  preview,
  alerts,
  onRemove,
  onCalculate,
}: {
  index: number;
  locked: boolean;
  selected: boolean;
  onSelect: () => void;
  rules: unknown;
  preview: CalculationRead | null;
  alerts: ReturnType<typeof placeAlerts>;
  onRemove: () => void;
  onCalculate: () => void;
}) {
  const t = useTranslations("prescriptions");
  const form = useFormContext<PrescriptionFormValues>();
  const item = form.watch(`items.${index}`);
  const indications = readIndicationCodes(rules);
  const storedTaper = readStoredTaper(rules);
  const volume = preview ? flagValue(preview, "volume_ml") : null;
  const volumeUnit = preview ? flagUnit(preview, "volume_ml") : null;
  const needsAllergy = alerts.some(
    (alert) => alert.code === "prescription.allergy_conflict",
  );
  const needsDose = alerts.some(
    (alert) => alert.code === "prescription.dose_above_maximum",
  );

  if (!item) {
    return null;
  }

  return (
    <fieldset
      className={`space-y-3 rounded-xl border p-4 ${selected ? "border-primary" : "border-border"}`}
      onFocus={onSelect}
    >
      <legend className="px-1 text-sm font-medium">
        {item.label || t("builder.title")}
      </legend>
      <SelectField
        name={`items.${index}.route`}
        label={t("item.route")}
        disabled={locked}
        options={["oral", "nasal", "otic", "topical", "injection"]
          .filter(isRoute)
          .map((route) => ({ value: route, label: routeLabel(t, route) }))}
      />
      {indications.length > 0 ? (
        <label className="block text-sm">
          {t("item.calculate")}
          <select
            className="mt-1 flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
            value={item.indicationCode}
            disabled={locked}
            onChange={(event) =>
              form.setValue(`items.${index}.indicationCode`, event.target.value)
            }
          >
            <option value="">{t("item.preview")}</option>
            {indications.map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      <TextField
        name={`items.${index}.doseAmount`}
        label={t("item.dose")}
        disabled={locked || item.calculateFromFormulary}
      />
      <TextField
        name={`items.${index}.doseUnit`}
        label={t("item.unit")}
        disabled={locked || item.calculateFromFormulary}
      />
      <TextField
        name={`items.${index}.frequencyPerDay`}
        label={t("item.frequency")}
        disabled={locked}
      />
      <TextField
        name={`items.${index}.durationDays`}
        label={t("item.duration")}
        disabled={locked}
      />
      <TextField
        name={`items.${index}.quantity`}
        label={t("item.quantity")}
        disabled={locked}
      />
      <TextAreaField
        name={`items.${index}.instructionsText`}
        label={t("item.instructions")}
        disabled={locked}
      />
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={item.isRenewable}
          disabled={locked}
          onChange={(event) =>
            form.setValue(`items.${index}.isRenewable`, event.target.checked)
          }
        />
        {t("item.renewable")}
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={item.substitutionAllowed}
          disabled={locked}
          onChange={(event) =>
            form.setValue(
              `items.${index}.substitutionAllowed`,
              event.target.checked,
            )
          }
        />
        {t("item.substitution")}
      </label>
      {item.formularyEntryPublicId ? (
        <Button
          type="button"
          variant="secondary"
          disabled={locked}
          onClick={onCalculate}
          {...testIdProps(testIds.prescriptions.calculateDose)}
        >
          {t("item.calculate")}
        </Button>
      ) : null}
      {storedTaper ? (
        <Button
          type="button"
          variant="secondary"
          disabled={locked}
          onClick={() => {
            form.setValue(`items.${index}.useFormularyTaper`, true);
            form.setValue(`items.${index}.taperStartMg`, "");
            form.setValue(`items.${index}.taperStepMg`, "");
            form.setValue(`items.${index}.taperDaysPerStep`, "");
            form.setValue(`items.${index}.taperMinimumMg`, "");
          }}
        >
          {t("item.formularyTaper")}
        </Button>
      ) : null}
      {preview ? (
        <p
          className="text-sm"
          {...testIdProps(testIds.prescriptions.dosePreview)}
        >
          {t("item.preview")}: {preview.value} {preview.unit}
          {volume ? ` / ${volume} ${volumeUnit ?? ""}` : ""}
        </p>
      ) : null}
      {alerts.map((alert) => (
        <p key={alert.code} className="text-sm text-destructive">
          {alertCopy(t, alert)}
        </p>
      ))}
      {needsAllergy ? (
        <TextField
          name={`items.${index}.allergyOverride`}
          label={t("item.overrideAllergy")}
          disabled={locked}
        />
      ) : null}
      {needsDose ? (
        <TextField
          name={`items.${index}.doseOverride`}
          label={t("item.overrideDose")}
          disabled={locked}
        />
      ) : null}
      <Button
        type="button"
        variant="ghost"
        disabled={locked}
        onClick={onRemove}
      >
        {t("item.remove")}
      </Button>
    </fieldset>
  );
}
