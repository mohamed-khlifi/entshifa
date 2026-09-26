"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useLocale, useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { DataTable } from "@/components/data/DataTable";
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
import type { TranslationCoverageItem } from "@/lib/api/generated";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

import { fetchTranslationCoverage } from "../api/terminology-admin.api";

export function TerminologyCoveragePanel() {
  const t = useTranslations("terminology");
  const locale = useLocale();
  const { session } = useSession();
  const [targetLocale, setTargetLocale] = useState("ar");
  const query = useQuery({
    queryKey: queryKeys.terminology.coverage(targetLocale),
    queryFn: () =>
      fetchTranslationCoverage(targetLocale, locale, session!.clinicPublicId, {
        limit: 50,
        offset: 0,
      }),
    enabled: Boolean(session?.clinicPublicId),
  });

  const columns = useMemo<ColumnDef<TranslationCoverageItem>[]>(
    () => [
      { accessorKey: "code", header: t("coverage.code") },
      { accessorKey: "kind", header: t("coverage.kind") },
      { accessorKey: "display", header: t("coverage.display") },
      { accessorKey: "usageCount", header: t("coverage.usage") },
    ],
    [t],
  );

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <Link
        href="/admin/terminology"
        className="text-sm text-primary hover:underline"
      >
        {t("nav.concepts")}
      </Link>
      <Card
        className="border-border/80 shadow-sm"
        {...testIdProps(testIds.terminology.coverage.root)}
      >
        <CardHeader>
          <CardTitle>{t("coverage.title")}</CardTitle>
          <CardDescription>{t("coverage.description")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="max-w-xs space-y-2">
            <Label htmlFor="coverage-locale">{t("coverage.locale")}</Label>
            <select
              id="coverage-locale"
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={targetLocale}
              onChange={(event) => setTargetLocale(event.target.value)}
              {...testIdProps(testIds.terminology.coverage.locale)}
            >
              <option value="en">en</option>
              <option value="fr">fr</option>
              <option value="ar">ar</option>
            </select>
          </div>
          <DataTable
            columns={columns}
            data={query.data?.items ?? []}
            totalItems={query.data?.page.total ?? query.data?.items.length ?? 0}
            getRowId={(row) => row.publicId}
            isLoading={query.isLoading}
            isError={query.isError}
            emptyTitle={t("coverage.emptyTitle")}
          />
        </CardContent>
      </Card>
    </div>
  );
}
