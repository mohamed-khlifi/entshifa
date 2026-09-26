"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useLocale, useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { DataTable } from "@/components/data/DataTable";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Link } from "@/lib/i18n/navigation";
import { queryKeys } from "@/lib/api/query-keys";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

import {
  createClinicConcept,
  fetchAdminConcepts,
  upsertClinicTranslation,
} from "../api/terminology-admin.api";
import type { ConceptAdminRead } from "@/lib/api/generated";

export function TerminologyConceptsPanel() {
  const t = useTranslations("terminology");
  const locale = useLocale();
  const { session } = useSession();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const page = Math.max(1, Number(searchParams.get("page") ?? "1") || 1);
  const pageSize = Math.max(
    1,
    Math.min(100, Number(searchParams.get("pageSize") ?? "20") || 20),
  );
  const q = (searchParams.get("q") ?? "").trim();
  const [showCreate, setShowCreate] = useState(false);
  const [code, setCode] = useState("");
  const [display, setDisplay] = useState("");
  const [selected, setSelected] = useState<ConceptAdminRead | null>(null);
  const [overrideDisplay, setOverrideDisplay] = useState("");

  const query = useQuery({
    queryKey: queryKeys.terminology.adminConcepts({
      q,
      limit: pageSize,
      offset: (page - 1) * pageSize,
    }),
    queryFn: () =>
      fetchAdminConcepts(locale, session!.clinicPublicId, {
        q: q || undefined,
        limit: pageSize,
        offset: (page - 1) * pageSize,
      }),
    enabled: Boolean(session?.clinicPublicId),
  });

  const create = useMutation({
    mutationFn: () =>
      createClinicConcept(
        { code, kind: "finding", locale, display, sortOrder: 0 },
        locale,
        session!.clinicPublicId,
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.terminology.all });
      toast.success(t("concepts.created"));
      setShowCreate(false);
      setCode("");
      setDisplay("");
    },
  });

  const rename = useMutation({
    mutationFn: () =>
      upsertClinicTranslation(
        selected!.publicId,
        locale,
        { display: overrideDisplay },
        locale,
        session!.clinicPublicId,
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.terminology.all });
      toast.success(t("concepts.renamed"));
    },
  });

  const columns = useMemo<ColumnDef<ConceptAdminRead>[]>(
    () => [
      { accessorKey: "code", header: t("concepts.code") },
      { accessorKey: "kind", header: t("concepts.kind") },
      {
        id: "owned",
        header: t("concepts.scope"),
        cell: ({ row }) =>
          row.original.clinicOwned ? t("concepts.clinic") : t("concepts.global"),
      },
      {
        id: "label",
        header: t("concepts.display"),
        cell: ({ row }) =>
          row.original.translations.find((item) => item.locale === locale)?.display ??
          row.original.translations[0]?.display ??
          "",
      },
    ],
    [locale, t],
  );

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap gap-3 text-sm">
        <Link href="/admin/terminology/coverage" className="text-primary hover:underline">
          {t("nav.coverage")}
        </Link>
        <Link href="/admin/terminology/value-sets" className="text-primary hover:underline">
          {t("nav.valueSets")}
        </Link>
      </div>
      <Card className="border-border/80 shadow-sm" {...testIdProps(testIds.terminology.concepts.root)}>
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-4">
          <div>
            <CardTitle>{t("concepts.title")}</CardTitle>
            <CardDescription>{t("concepts.description")}</CardDescription>
          </div>
          <Button type="button" onClick={() => setShowCreate((value) => !value)} {...testIdProps(testIds.terminology.concepts.createOpen)}>
            {t("concepts.create")}
          </Button>
        </CardHeader>
        <CardContent className="space-y-6">
          {showCreate ? (
            <div className="grid gap-4 rounded-lg border border-border bg-muted/20 p-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="concept-code">{t("concepts.code")}</Label>
                <Input id="concept-code" value={code} onChange={(e) => setCode(e.target.value)} {...testIdProps(testIds.terminology.concepts.code)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="concept-display">{t("concepts.display")}</Label>
                <Input id="concept-display" value={display} onChange={(e) => setDisplay(e.target.value)} {...testIdProps(testIds.terminology.concepts.display)} />
              </div>
              <Button type="button" disabled={!code || !display || create.isPending} onClick={() => void create.mutateAsync()} {...testIdProps(testIds.terminology.concepts.createSubmit)}>
                {t("concepts.createSubmit")}
              </Button>
            </div>
          ) : null}
          <DataTable
            columns={columns}
            data={query.data?.items ?? []}
            totalItems={query.data?.page.total ?? query.data?.items.length ?? 0}
            getRowId={(row) => row.publicId}
            isLoading={query.isLoading}
            isError={query.isError}
            emptyTitle={t("concepts.emptyTitle")}
          />
          <div className="grid gap-3 rounded-lg border border-border p-4">
            <Label htmlFor="concept-select">{t("concepts.rename")}</Label>
            <select
              id="concept-select"
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={selected?.publicId ?? ""}
              onChange={(event) => {
                const next = query.data?.items.find((item) => item.publicId === event.target.value) ?? null;
                setSelected(next);
                const current = next?.translations.find((item) => item.locale === locale && item.clinicOwned);
                setOverrideDisplay(current?.display ?? "");
              }}
              {...testIdProps(testIds.terminology.concepts.select)}
            >
              <option value="" />
              {(query.data?.items ?? []).map((item) => (
                <option key={item.publicId} value={item.publicId}>
                  {item.code}
                </option>
              ))}
            </select>
            <Input value={overrideDisplay} onChange={(e) => setOverrideDisplay(e.target.value)} {...testIdProps(testIds.terminology.concepts.override)} />
            <Button type="button" disabled={!selected || !overrideDisplay || rename.isPending} onClick={() => void rename.mutateAsync()} {...testIdProps(testIds.terminology.concepts.renameSubmit)}>
              {t("concepts.renameSubmit")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
