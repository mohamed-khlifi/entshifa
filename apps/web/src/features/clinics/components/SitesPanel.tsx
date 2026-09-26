"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";

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
import {
  useCreateSiteMutation,
  useSitesQuery,
} from "@/features/clinics/hooks/use-clinic-queries";
import type { SiteRead } from "@/lib/api/generated";
import { testIdProps, testIds } from "@/lib/test/test-id";

export function SitesPanel() {
  const t = useTranslations("clinics");
  const { data, isLoading, isError } = useSitesQuery({ limit: 50, offset: 0 });
  const createSite = useCreateSiteMutation();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [city, setCity] = useState("");

  const columns = useMemo<ColumnDef<SiteRead>[]>(
    () => [
      { accessorKey: "name", header: t("sites.name") },
      { accessorKey: "city", header: t("sites.city") },
      { accessorKey: "phone", header: t("sites.phone") },
      {
        accessorKey: "isPrimary",
        header: t("sites.primary"),
        cell: ({ row }) => (row.original.isPrimary ? "✓" : ""),
      },
    ],
    [t],
  );

  const onCreate = async () => {
    await createSite.mutateAsync({ name, city: city || null, isPrimary: false });
    setName("");
    setCity("");
    setShowCreate(false);
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Card className="border-border/80 shadow-sm">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-4">
          <div>
            <CardTitle>{t("sites.title")}</CardTitle>
            <CardDescription>{t("sites.description")}</CardDescription>
          </div>
          <Button
            type="button"
            onClick={() => setShowCreate((v) => !v)}
            {...testIdProps(testIds.clinics.siteCreate)}
          >
            {t("sites.add")}
          </Button>
        </CardHeader>
        <CardContent className="space-y-6">
          {showCreate ? (
            <div className="grid gap-4 rounded-lg border border-border bg-muted/20 p-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="site-name">{t("sites.name")}</Label>
                <Input
                  id="site-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="site-city">{t("sites.city")}</Label>
                <Input
                  id="site-city"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                />
              </div>
              <div className="sm:col-span-2">
                <Button
                  type="button"
                  onClick={() => void onCreate()}
                  disabled={!name || createSite.isPending}
                >
                  {t("sites.createSubmit")}
                </Button>
              </div>
            </div>
          ) : null}
          <div {...testIdProps(testIds.clinics.sitesTable)}>
            <DataTable
              columns={columns}
              data={data?.items ?? []}
              totalItems={data?.page.total ?? data?.items.length ?? 0}
              getRowId={(row) => row.publicId}
              isLoading={isLoading}
              isError={isError}
              emptyTitle={t("sites.title")}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
