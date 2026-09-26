"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import {
  useClinicalSettingsQuery,
  useUpdateClinicalSettingsMutation,
} from "@/features/clinics/hooks/use-clinic-queries";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { testIdProps, testIds } from "@/lib/test/test-id";

export function ClinicalSettingsPanel() {
  const t = useTranslations("clinics");
  const { data, isLoading } = useClinicalSettingsQuery();
  const save = useUpdateClinicalSettingsMutation();
  const [draft, setDraft] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!data) return;
    const next: Record<string, string> = {};
    for (const item of data.items) {
      next[item.key] = JSON.stringify(item.value);
    }
    setDraft(next);
  }, [data]);

  const onSave = () => {
    if (!data) return;
    const items = data.items.map((item) => ({
      key: item.key,
      value: JSON.parse(draft[item.key] ?? "null") as unknown,
    }));
    void save.mutateAsync({ items });
  };

  if (isLoading || !data) {
    return null;
  }

  return (
    <div className="mx-auto max-w-3xl">
      <Card
        className="border-border/80 shadow-sm"
        {...testIdProps(testIds.clinics.clinicalForm)}
      >
        <CardHeader>
          <CardTitle>{t("clinical.title")}</CardTitle>
          <CardDescription>{t("clinical.description")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {data.items.map((item) => (
            <div key={item.key} className="space-y-2">
              <Label>
                {t(`clinical.keys.${item.key}` as "clinical.keys.pta_formula")}
              </Label>
              <p className="text-xs text-muted-foreground">
                {t("clinical.source", { source: item.source })}
              </p>
              <textarea
                className="min-h-[72px] w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-xs shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={draft[item.key] ?? ""}
                onChange={(e) =>
                  setDraft((prev) => ({ ...prev, [item.key]: e.target.value }))
                }
              />
            </div>
          ))}
          <Button
            type="button"
            onClick={onSave}
            disabled={save.isPending}
            {...testIdProps(testIds.clinics.clinicalSave)}
          >
            {t("clinical.save")}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
