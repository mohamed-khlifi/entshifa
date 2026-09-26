"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useLocale, useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { DataTable } from "@/components/data/DataTable";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { PATIENT_FLAG_CODES, SEX_VALUES } from "../constants";
import { usePatientsQuery } from "../hooks/use-patient-queries";
import { flagLabel, sexLabel } from "../lib/labels";
import type { PatientSummaryRead } from "@/lib/api/generated";
import { formatDate, formatPersonName } from "@/lib/i18n/format";
import { Link, usePathname, useRouter } from "@/lib/i18n/navigation";
import { Permission } from "@/lib/permissions";
import { patientRowTestId, testIdProps, testIds } from "@/lib/test/test-id";
import { usePermission } from "@/providers/permission-provider";

export function PatientsListPanel() {
  const t = useTranslations("patients");
  const locale = useLocale();
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const canWrite = usePermission(Permission.PATIENT_WRITE);
  const page = Math.max(1, Number(searchParams.get("page") ?? "1") || 1);
  const pageSize = Math.max(
    1,
    Math.min(100, Number(searchParams.get("pageSize") ?? "20") || 20),
  );
  const search = (searchParams.get("q") ?? "").trim();
  const sex = searchParams.get("sex") ?? "";
  const birthDate = searchParams.get("birthDate") ?? "";
  const flagCode = searchParams.get("flagCode") ?? "";
  const sortBy = searchParams.get("sortBy");
  const sortDir = searchParams.get("sortDir") === "desc" ? "desc" : "asc";
  const sort = sortBy ? `${sortDir === "desc" ? "-" : ""}${sortBy}` : undefined;

  const { data, isLoading, isError } = usePatientsQuery({
    limit: pageSize,
    offset: (page - 1) * pageSize,
    search: search || undefined,
    sex: sex || undefined,
    birthDate: birthDate || undefined,
    flagCode: flagCode || undefined,
    sort,
  });

  const setFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    params.set("page", "1");
    router.replace(`${pathname}?${params.toString()}`);
  };

  const columns = useMemo<ColumnDef<PatientSummaryRead>[]>(
    () => [
      {
        id: "lastName",
        header: t("list.name"),
        cell: ({ row }) => (
          <Link
            href={`/patients/${row.original.publicId}`}
            className="font-medium underline"
          >
            {formatPersonName(
              { given: row.original.firstName, family: row.original.lastName },
              locale,
            )}
          </Link>
        ),
      },
      { accessorKey: "mrn", header: t("list.mrn") },
      {
        id: "sex",
        header: t("list.sex"),
        cell: ({ row }) => sexLabel(t, row.original.sex),
      },
      {
        id: "birthDate",
        header: t("list.birthDate"),
        cell: ({ row }) => formatDate(row.original.birthDate, locale),
      },
      {
        id: "phonePrimary",
        header: t("list.phone"),
        cell: ({ row }) => row.original.phonePrimary ?? "",
      },
    ],
    [locale, t],
  );

  return (
    <div className="space-y-4" {...testIdProps(testIds.patients.list)}>
      {canWrite ? (
        <div className="flex justify-end">
          <Button asChild>
            <Link
              href="/patients/new"
              {...testIdProps(testIds.patients.create)}
            >
              {t("list.create")}
            </Link>
          </Button>
        </div>
      ) : null}
      <DataTable
        columns={columns}
        data={data?.items ?? []}
        totalItems={data?.page.total ?? 0}
        getRowId={(row) => row.publicId}
        getRowTestId={patientRowTestId}
        isLoading={isLoading}
        isError={isError}
        errorMessage={t("list.error")}
        emptyTitle={t("list.emptyTitle")}
        emptyDescription={t("list.emptyDescription")}
        defaultPageSize={20}
        toolbar={
          <div className="flex flex-wrap items-end gap-3">
            <div className="w-40 space-y-1.5">
              <Label htmlFor={testIds.patients.filterSex}>
                {t("list.filters.sex")}
              </Label>
              <Select
                id={testIds.patients.filterSex}
                value={sex}
                onChange={(event) => setFilter("sex", event.target.value)}
                {...testIdProps(testIds.patients.filterSex)}
              >
                <option value="">{t("list.filters.any")}</option>
                {SEX_VALUES.map((value) => (
                  <option key={value} value={value}>
                    {sexLabel(t, value)}
                  </option>
                ))}
              </Select>
            </div>
            <div className="w-44 space-y-1.5">
              <Label htmlFor={testIds.patients.filterBirthDate}>
                {t("list.filters.birthDate")}
              </Label>
              <input
                id={testIds.patients.filterBirthDate}
                type="date"
                className="flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={birthDate}
                onChange={(event) => setFilter("birthDate", event.target.value)}
                {...testIdProps(testIds.patients.filterBirthDate)}
              />
            </div>
            <div className="min-w-52 space-y-1.5">
              <Label htmlFor={testIds.patients.filterFlag}>
                {t("list.filters.flag")}
              </Label>
              <Select
                id={testIds.patients.filterFlag}
                value={flagCode}
                onChange={(event) => setFilter("flagCode", event.target.value)}
                {...testIdProps(testIds.patients.filterFlag)}
              >
                <option value="">{t("list.filters.any")}</option>
                {PATIENT_FLAG_CODES.map((code) => (
                  <option key={code} value={code}>
                    {flagLabel(t, code)}
                  </option>
                ))}
              </Select>
            </div>
          </div>
        }
      />
    </div>
  );
}
