"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "@/lib/i18n/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Controller, FormProvider, useForm } from "react-hook-form";

import { EmptyState } from "@/components/data/EmptyState";
import { FormFieldShell } from "@/components/forms/FormFieldShell";
import { TextField } from "@/components/forms/TextField";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import {
  useCalculatorSpec,
  useCalculatorsList,
  useEvaluateCalculator,
} from "@/features/calculators/hooks/use-calculators";
import {
  buildCalculatorFormSchema,
  defaultValuesFromSpec,
} from "@/features/calculators/schemas/calculator.schema";
import {
  calculatorMessageKey,
  calculatorTitle,
} from "@/features/calculators/lib/labels";
import type { CalculationResultRead } from "@/features/calculators/types/calculator.types";
import { cn } from "@/lib/utils/cn";
import {
  calculatorFieldTestId,
  calculatorNavItemTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

type CalculatorWorkspaceProps = {
  slug?: string;
  patientId?: string;
  encounterId?: string;
};

export function CalculatorWorkspace({
  slug,
  patientId,
  encounterId,
}: CalculatorWorkspaceProps) {
  const t = useTranslations("calculators");
  const tDomain = useTranslations("calculators.domains");
  const router = useRouter();
  const listQuery = useCalculatorsList();
  const specQuery = useCalculatorSpec(slug);
  const evaluateMutation = useEvaluateCalculator(slug ?? "");
  const [result, setResult] = useState<CalculationResultRead | null>(null);
  const [saveToChart, setSaveToChart] = useState(Boolean(patientId));

  const spec = specQuery.data;
  const schema = useMemo(
    () => (spec ? buildCalculatorFormSchema(spec.inputs) : null),
    [spec],
  );
  const form = useForm({
    resolver: schema ? zodResolver(schema) : undefined,
    defaultValues: spec ? defaultValuesFromSpec(spec.inputs) : {},
    mode: "onBlur",
  });

  useEffect(() => {
    if (!spec) {
      return;
    }
    form.reset(defaultValuesFromSpec(spec.inputs));
    setResult(null);
  }, [spec, form]);

  const grouped = useMemo(() => {
    const items = listQuery.data?.items ?? [];
    const map = new Map<string, typeof items>();
    for (const item of items) {
      const bucket = map.get(item.domain) ?? [];
      bucket.push(item);
      map.set(item.domain, bucket);
    }
    return map;
  }, [listQuery.data?.items]);

  const handleSelect = (code: string) => {
    router.push(
      patientId
        ? `/calculators/${code}?patientId=${patientId}${encounterId ? `&encounterId=${encounterId}` : ""}`
        : `/calculators/${code}`,
    );
  };

  const onSubmit = form.handleSubmit(async (values) => {
    if (!slug) {
      return;
    }
    const inputs: Record<string, string | number | boolean> = {};
    for (const [key, value] of Object.entries(values)) {
      if (value === undefined || value === "") {
        continue;
      }
      inputs[key] = value as string | number | boolean;
    }
    const next = await evaluateMutation.mutateAsync({
      inputs,
      saveToConsultation: saveToChart && Boolean(patientId),
      patientId: saveToChart ? (patientId ?? null) : null,
      encounterId: saveToChart ? (encounterId ?? null) : null,
    });
    setResult(next);
  });

  return (
    <div
      className="grid gap-6 lg:grid-cols-[minmax(220px,280px)_1fr]"
      {...testIdProps(testIds.calculators.workspace)}
    >
      <Card className="p-4">
        <p className="mb-3 text-sm font-medium text-muted-foreground">
          {t("page.title")}
        </p>
        <nav className="flex flex-col gap-3">
          {listQuery.isLoading ? (
            <p
              className="text-sm text-muted-foreground"
              {...testIdProps(testIds.calculators.loading)}
            >
              {t("loading")}
            </p>
          ) : null}
          {[...grouped.entries()].map(([domain, items]) => (
            <div key={domain}>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {tDomain.has(domain) ? tDomain(domain) : domain}
              </p>
              <ul className="flex flex-col gap-0.5">
                {items.map((item) => (
                  <li key={item.code}>
                    <button
                      type="button"
                      className={cn(
                        "w-full rounded-lg px-2 py-1.5 text-start text-sm transition-colors",
                        item.code === slug
                          ? "bg-primary/10 font-medium text-primary"
                          : "text-foreground hover:bg-muted",
                      )}
                      onClick={() => handleSelect(item.code)}
                      {...testIdProps(calculatorNavItemTestId(item.code))}
                    >
                      {calculatorTitle(t, item.code)}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </Card>

      <CalculatorDetailPanel
        slug={slug}
        spec={spec}
        isLoading={specQuery.isLoading}
        selectPrompt={t("selectPrompt")}
      >
        {spec ? (
          <FormProvider {...form}>
            <form className="space-y-6" onSubmit={onSubmit}>
              <header className="space-y-1">
                <h2 className="text-lg font-semibold tracking-tight">
                  {calculatorTitle(t, spec.code)}
                </h2>
                <p className="text-sm text-muted-foreground">{spec.formula}</p>
                <p className="text-xs text-muted-foreground">
                  {spec.reference}
                </p>
              </header>

              <CalculatorFields spec={spec} t={t} form={form} />

              {patientId ? (
                <Card className="space-y-3 p-4">
                  <p className="text-sm font-medium">{t("save.title")}</p>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="calc-save-chart"
                      checked={saveToChart}
                      onChange={(event) => setSaveToChart(event.target.checked)}
                      className="size-4 rounded border-input"
                      {...testIdProps(testIds.calculators.saveToggle)}
                    />
                    <Label htmlFor="calc-save-chart">
                      {t("actions.saveToConsultation")}
                    </Label>
                  </div>
                </Card>
              ) : null}

              <div className="flex flex-wrap gap-2">
                <Button
                  type="submit"
                  disabled={evaluateMutation.isPending}
                  {...testIdProps(testIds.calculators.submit)}
                >
                  {t("actions.calculate")}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => form.reset(defaultValuesFromSpec(spec.inputs))}
                  {...testIdProps(testIds.calculators.reset)}
                >
                  {t("actions.reset")}
                </Button>
              </div>

              {result ? (
                <CalculatorResultCard result={result} />
              ) : (
                <EmptyState
                  title={t("empty.result")}
                  {...testIdProps(testIds.calculators.resultEmpty)}
                />
              )}
            </form>
          </FormProvider>
        ) : null}
      </CalculatorDetailPanel>
    </div>
  );
}

function CalculatorDetailPanel({
  slug,
  spec,
  isLoading,
  children,
  selectPrompt,
}: {
  slug?: string;
  spec: ReturnType<typeof useCalculatorSpec>["data"];
  isLoading: boolean;
  children: ReactNode;
  selectPrompt: string;
}) {
  if (!slug) {
    return (
      <Card className="p-6">
        <EmptyState title={selectPrompt} />
      </Card>
    );
  }
  if (isLoading || !spec) {
    return (
      <Card className="p-6">
        <p className="text-sm text-muted-foreground">…</p>
      </Card>
    );
  }
  return <Card className="p-6">{children}</Card>;
}

function CalculatorFields({
  spec,
  t,
  form,
}: {
  spec: NonNullable<ReturnType<typeof useCalculatorSpec>["data"]>;
  t: ReturnType<typeof useTranslations<"calculators">>;
  form: ReturnType<typeof useForm>;
}) {
  return (
    <div
      className="grid gap-4 sm:grid-cols-2"
      {...testIdProps(testIds.calculators.form)}
    >
      {spec.inputs.map((field) => {
        const label = t(calculatorMessageKey(field.labelKey) as never);
        const testProps = testIdProps(calculatorFieldTestId(field.name));
        if (field.kind === "select") {
          return (
            <Controller
              key={field.name}
              control={form.control}
              name={field.name}
              render={({ field: control }) => (
                <FormFieldShell
                  name={field.name}
                  htmlFor={field.name}
                  label={label}
                  required={field.required}
                  className="sm:col-span-2"
                >
                  <Select
                    id={field.name}
                    value={control.value ? String(control.value) : ""}
                    onChange={(event) => control.onChange(event.target.value)}
                    {...testProps}
                  >
                    {!field.defaultValue ? (
                      <option value="" disabled={field.required}>
                        {t("selectPlaceholder")}
                      </option>
                    ) : null}
                    {field.options.map((option) => (
                      <option key={option.value} value={option.value}>
                        {t(calculatorMessageKey(option.labelKey) as never)}
                      </option>
                    ))}
                  </Select>
                </FormFieldShell>
              )}
            />
          );
        }
        if (field.kind === "boolean") {
          return (
            <Controller
              key={field.name}
              control={form.control}
              name={field.name}
              render={({ field: control }) => (
                <div className="flex items-center gap-2 sm:col-span-2">
                  <input
                    type="checkbox"
                    id={field.name}
                    checked={Boolean(control.value)}
                    onChange={(event) => control.onChange(event.target.checked)}
                    className="size-4 rounded border-input"
                    {...testProps}
                  />
                  <Label htmlFor={field.name}>{label}</Label>
                </div>
              )}
            />
          );
        }
        return (
          <TextField
            key={field.name}
            name={field.name}
            label={label}
            required={field.required}
            unit={field.unit ?? undefined}
            type={field.kind === "date" ? "text" : "text"}
            {...testProps}
          />
        );
      })}
    </div>
  );
}

function CalculatorResultCard({ result }: { result: CalculationResultRead }) {
  const t = useTranslations("calculators");
  return (
    <Card className="space-y-3 border-primary/20 bg-primary/5 p-4">
      <p className="text-sm font-medium text-muted-foreground">
        {t("result.title")}
      </p>
      <p
        className="text-3xl font-semibold tracking-tight"
        {...testIdProps(testIds.calculators.resultValue)}
      >
        {result.value}
        {result.unit ? (
          <span className="ms-2 text-base font-normal text-muted-foreground">
            {result.unit}
          </span>
        ) : null}
      </p>
      <dl className="grid gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-muted-foreground">{t("result.formula")}</dt>
          <dd>{result.formula}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">{t("result.version")}</dt>
          <dd>{result.version}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-muted-foreground">{t("result.reference")}</dt>
          <dd>{result.reference}</dd>
        </div>
      </dl>
      {result.flags.length > 0 ? (
        <div {...testIdProps(testIds.calculators.flags)}>
          <p className="mb-1 text-sm font-medium">{t("flags.title")}</p>
          <ul className="list-inside list-disc text-sm text-muted-foreground">
            {result.flags.map((flag) => (
              <li key={flag.code}>{flag.code}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </Card>
  );
}
