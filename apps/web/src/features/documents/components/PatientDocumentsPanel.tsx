"use client";

import { useMemo, useRef, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { useTranslations } from "next-intl";

import { DataTable } from "@/components/data";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import type { DocumentRead } from "@/lib/api/generated";
import { publicIdTestId, testIdProps, testIds } from "@/lib/test/test-id";

import {
  useCreateDocumentMutation,
  useDocumentDownload,
  useDocumentPreviewQuery,
  useDocumentTemplatesQuery,
  useFinalizeDocumentMutation,
  usePatientDocumentsQuery,
} from "../hooks/use-document-queries";
import {
  documentCategoryLabel,
  documentLocaleLabel,
  documentStatusLabel,
} from "../lib/labels";

const LOCALES = ["en", "fr", "ar"] as const;

export function PatientDocumentsPanel({
  patientPublicId,
}: {
  patientPublicId: string;
}) {
  const t = useTranslations("documents");
  const templates = useDocumentTemplatesQuery();
  const documents = usePatientDocumentsQuery(patientPublicId);
  const create = useCreateDocumentMutation(patientPublicId);
  const finalize = useFinalizeDocumentMutation(patientPublicId);
  const download = useDocumentDownload();
  const [templateCode, setTemplateCode] = useState("patient_summary");
  const [locale, setLocale] = useState<(typeof LOCALES)[number]>("en");
  const [selectedId, setSelectedId] = useState("");
  const frameRef = useRef<HTMLIFrameElement>(null);
  const preview = useDocumentPreviewQuery(selectedId, selectedId.length > 0);
  const rows = documents.data?.items ?? [];
  const selected = rows.find((row) => row.publicId === selectedId);

  const columns = useMemo<ColumnDef<DocumentRead>[]>(
    () => [
      {
        id: "title",
        accessorKey: "title",
        header: t("columns.title"),
      },
      {
        id: "status",
        accessorKey: "status",
        header: t("columns.status"),
        cell: ({ row }) => documentStatusLabel(t, row.original.status),
      },
      {
        id: "locale",
        accessorKey: "locale",
        header: t("columns.locale"),
        cell: ({ row }) => documentLocaleLabel(t, row.original.locale),
      },
      {
        id: "open",
        header: t("list.preview"),
        cell: ({ row }) => (
          <Button
            type="button"
            variant="secondary"
            onClick={() => setSelectedId(row.original.publicId)}
            {...testIdProps(
              publicIdTestId("documents.open", row.original.publicId),
            )}
          >
            {t("list.preview")}
          </Button>
        ),
      },
    ],
    [t],
  );

  return (
    <section className="space-y-4" {...testIdProps(testIds.documents.list)}>
      <h1 className="text-xl font-semibold">{t("list.title")}</h1>
      <div className="flex flex-wrap items-end gap-3">
        <div className="space-y-2">
          <Label htmlFor="document-template">{t("list.template")}</Label>
          <Select
            id="document-template"
            value={templateCode}
            onChange={(event) => setTemplateCode(event.target.value)}
            {...testIdProps(testIds.documents.templateSelect)}
          >
            {(templates.data?.items ?? []).map((item) => (
              <option key={item.publicId} value={item.code}>
                {`${documentCategoryLabel(t, item.category)} · ${item.code}`}
              </option>
            ))}
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="document-locale">{t("list.locale")}</Label>
          <Select
            id="document-locale"
            value={locale}
            onChange={(event) =>
              setLocale(event.target.value as (typeof LOCALES)[number])
            }
            {...testIdProps(testIds.documents.localeSelect)}
          >
            {LOCALES.map((code) => (
              <option key={code} value={code}>
                {documentLocaleLabel(t, code)}
              </option>
            ))}
          </Select>
        </div>
        <Button
          type="button"
          disabled={create.isPending}
          onClick={() =>
            void create.mutate({
              patientPublicId,
              templateCode,
              locale,
            })
          }
          {...testIdProps(testIds.documents.create)}
        >
          {t("list.create")}
        </Button>
      </div>
      <DataTable
        columns={columns}
        data={rows}
        totalItems={documents.data?.page.total ?? rows.length}
        getRowId={(row) => row.publicId}
        isLoading={documents.isLoading}
        isError={documents.isError}
        errorMessage={t("list.error")}
        emptyTitle={t("list.empty")}
        emptyDescription={documents.isLoading ? t("list.loading") : undefined}
        getRowTestId={(rowId) => publicIdTestId("documents.row", rowId)}
      />
      {selected ? (
        <div className="space-y-3" {...testIdProps(testIds.documents.preview)}>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => frameRef.current?.contentWindow?.print()}
              {...testIdProps(testIds.documents.print)}
            >
              {t("list.print")}
            </Button>
            {selected.status === "draft" ? (
              <Button
                type="button"
                disabled={finalize.isPending}
                onClick={() => void finalize.mutate(selected.publicId)}
                {...testIdProps(testIds.documents.finalize)}
              >
                {t("list.finalize")}
              </Button>
            ) : null}
            {selected.status === "final" ? (
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  void download(selected.publicId).then((result) => {
                    window.open(result.url, "_blank", "noopener,noreferrer");
                  });
                }}
                {...testIdProps(testIds.documents.download)}
              >
                {t("list.download")}
              </Button>
            ) : null}
            <Button
              type="button"
              variant="ghost"
              onClick={() => setSelectedId("")}
            >
              {t("list.close")}
            </Button>
          </div>
          <iframe
            ref={frameRef}
            title={t("list.preview")}
            sandbox="allow-modals allow-same-origin"
            className="h-[640px] w-full rounded-lg border border-border bg-white"
            srcDoc={preview.data?.html ?? ""}
            {...testIdProps(testIds.documents.previewFrame)}
          />
        </div>
      ) : null}
    </section>
  );
}
