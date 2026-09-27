"use client";

import { useEffect, useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { useTranslations } from "next-intl";

import { DataTable } from "@/components/data";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import type {
  DocumentTemplateCreate,
  DocumentTemplateRead,
} from "@/lib/api/generated";
import {
  publicIdTestId,
  testId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

import {
  useCopyTemplateMutation,
  useDocumentTemplateQuery,
  useDocumentTemplatesQuery,
  usePublishTemplateVersionMutation,
  useTemplatePreviewMutation,
} from "../hooks/use-document-queries";
import { documentCategoryLabel, documentLocaleLabel } from "../lib/labels";
import { insertAtSelection, placeholderToken } from "../lib/insert-placeholder";

const LOCALES = ["en", "fr", "ar"] as const;

const TEMPLATE_CATEGORIES = [
  "consultation_report",
  "endoscopy_report",
  "audiology_report",
  "prescription",
  "certificate",
  "imaging_request",
  "referral_letter",
  "handout",
  "consent",
  "quote",
  "operative_note",
  "tumor_board",
  "patient_summary",
] as const satisfies readonly DocumentTemplateCreate["category"][];

function isTemplateCategory(
  value: string,
): value is DocumentTemplateCreate["category"] {
  return (TEMPLATE_CATEGORIES as readonly string[]).includes(value);
}

export function TemplateAdminPanel() {
  const t = useTranslations("documents");
  const templates = useDocumentTemplatesQuery();
  const [templateId, setTemplateId] = useState("");
  const detail = useDocumentTemplateQuery(templateId);
  const [locale, setLocale] = useState<(typeof LOCALES)[number]>("en");
  const [header, setHeader] = useState("");
  const [body, setBody] = useState("");
  const [footer, setFooter] = useState("");
  const [css, setCss] = useState("");
  const [previewHtml, setPreviewHtml] = useState("");
  const preview = useTemplatePreviewMutation();
  const publish = usePublishTemplateVersionMutation(templateId);
  const copy = useCopyTemplateMutation();
  const version = detail.data?.versions
    .filter((item) => item.locale === locale)
    .sort((left, right) => right.version - left.version)[0];

  useEffect(() => {
    setHeader(version?.headerHtml ?? "");
    setBody(version?.bodyHtml ?? "");
    setFooter(version?.footerHtml ?? "");
    setCss(version?.css ?? "");
    setPreviewHtml("");
  }, [
    version?.headerHtml,
    version?.bodyHtml,
    version?.footerHtml,
    version?.css,
    locale,
  ]);

  const columns = useMemo<ColumnDef<DocumentTemplateRead>[]>(
    () => [
      { id: "code", accessorKey: "code", header: t("columns.code") },
      {
        id: "category",
        accessorKey: "category",
        header: t("columns.category"),
        cell: ({ row }) => documentCategoryLabel(t, row.original.category),
      },
    ],
    [t],
  );

  const placeholders = detail.data?.placeholders ?? {};
  const locked = Boolean(detail.data?.isSystem);

  const refreshPreview = () => {
    if (!detail.data) return;
    void preview
      .mutateAsync({
        locale,
        direction: locale === "ar" ? "rtl" : "ltr",
        headerHtml: header,
        bodyHtml: body || "<p></p>",
        footerHtml: footer,
        css,
        placeholders,
        pageSetup: {
          title: version?.pageSetup.title ?? detail.data.code,
          size: "A4",
          orientation: "portrait",
          marginTopMm: 16,
          marginBottomMm: 16,
          marginLeftMm: 14,
          marginRightMm: 14,
        },
      })
      .then((result) => setPreviewHtml(result.html));
  };

  return (
    <section className="space-y-6" {...testIdProps(testIds.documents.editor)}>
      <h1 className="text-xl font-semibold">{t("editor.title")}</h1>
      <DataTable
        columns={columns}
        data={templates.data?.items ?? []}
        totalItems={templates.data?.page.total ?? 0}
        getRowId={(row) => row.publicId}
        isLoading={templates.isLoading}
        isError={templates.isError}
        errorMessage={t("editor.loadError")}
        emptyTitle={t("editor.empty")}
      />
      <div className="flex flex-wrap gap-2">
        {(templates.data?.items ?? []).map((item) => (
          <Button
            key={item.publicId}
            type="button"
            variant={item.publicId === templateId ? "default" : "secondary"}
            onClick={() => setTemplateId(item.publicId)}
            {...testIdProps(
              publicIdTestId("documents.template", item.publicId),
            )}
          >
            {documentCategoryLabel(t, item.category)}
          </Button>
        ))}
      </div>
      {detail.data ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-3">
            {locked ? (
              <p className="text-sm text-muted-foreground">
                {t("editor.systemLocked")}
              </p>
            ) : null}
            <div className="space-y-2">
              <Label htmlFor="template-locale">{t("editor.locale")}</Label>
              <Select
                id="template-locale"
                value={locale}
                onChange={(event) =>
                  setLocale(event.target.value as (typeof LOCALES)[number])
                }
                {...testIdProps(testIds.documents.editorLocale)}
              >
                {LOCALES.map((code) => (
                  <option key={code} value={code}>
                    {documentLocaleLabel(t, code)}
                  </option>
                ))}
              </Select>
            </div>
            <Label htmlFor="template-header">{t("editor.header")}</Label>
            <textarea
              id="template-header"
              className="min-h-16 w-full rounded-md border border-input px-3 py-2 text-sm"
              value={header}
              onChange={(event) => setHeader(event.target.value)}
              {...testIdProps(testIds.documents.editorHeader)}
            />
            <Label htmlFor="template-body">{t("editor.body")}</Label>
            <textarea
              id="template-body"
              className="min-h-48 w-full rounded-md border border-input px-3 py-2 font-mono text-sm"
              value={body}
              onChange={(event) => setBody(event.target.value)}
              {...testIdProps(testIds.documents.editorBody)}
            />
            <p className="text-sm font-medium">{t("editor.placeholders")}</p>
            <div className="flex flex-wrap gap-2">
              {Object.keys(placeholders).map((path) => (
                <Button
                  key={path}
                  type="button"
                  variant="secondary"
                  onClick={() => {
                    const field = document.getElementById("template-body");
                    if (!(field instanceof HTMLTextAreaElement)) return;
                    const next = insertAtSelection(
                      body,
                      field.selectionStart,
                      field.selectionEnd,
                      placeholderToken(path),
                    );
                    setBody(next.value);
                  }}
                  {...testIdProps(
                    testId(
                      "documents",
                      "placeholder",
                      path
                        .replace(/([a-z])([A-Z])/g, "$1-$2")
                        .replaceAll(".", "-")
                        .toLowerCase(),
                    ),
                  )}
                >
                  {path}
                </Button>
              ))}
            </div>
            <Label htmlFor="template-footer">{t("editor.footer")}</Label>
            <textarea
              id="template-footer"
              className="min-h-16 w-full rounded-md border border-input px-3 py-2 text-sm"
              value={footer}
              onChange={(event) => setFooter(event.target.value)}
              {...testIdProps(testIds.documents.editorFooter)}
            />
            <Label htmlFor="template-css">{t("editor.css")}</Label>
            <textarea
              id="template-css"
              className="min-h-16 w-full rounded-md border border-input px-3 py-2 font-mono text-sm"
              value={css}
              onChange={(event) => setCss(event.target.value)}
              {...testIdProps(testIds.documents.editorCss)}
            />
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="secondary"
                onClick={refreshPreview}
                {...testIdProps(testIds.documents.editorPreview)}
              >
                {t("editor.preview")}
              </Button>
              {locked && isTemplateCategory(detail.data.category) ? (
                <Button
                  type="button"
                  disabled={copy.isPending}
                  onClick={() => {
                    if (
                      !detail.data ||
                      !isTemplateCategory(detail.data.category)
                    ) {
                      return;
                    }
                    void copy.mutate({
                      code: detail.data.code,
                      category: detail.data.category,
                      placeholders,
                    });
                  }}
                  {...testIdProps(testIds.documents.copy)}
                >
                  {t("editor.copy")}
                </Button>
              ) : (
                <Button
                  type="button"
                  disabled={publish.isPending || body.trim().length === 0}
                  onClick={() =>
                    void publish.mutate({
                      locale,
                      direction: locale === "ar" ? "rtl" : "ltr",
                      headerHtml: header,
                      bodyHtml: body,
                      footerHtml: footer,
                      css,
                      pageSetup: {
                        title: version?.pageSetup.title ?? detail.data.code,
                        size: "A4",
                        orientation: "portrait",
                        marginTopMm: 16,
                        marginBottomMm: 16,
                        marginLeftMm: 14,
                        marginRightMm: 14,
                      },
                    })
                  }
                  {...testIdProps(testIds.documents.editorSave)}
                >
                  {t("editor.save")}
                </Button>
              )}
            </div>
          </div>
          <iframe
            title={t("editor.preview")}
            sandbox="allow-modals allow-same-origin"
            className="h-[720px] w-full rounded-lg border border-border bg-white"
            srcDoc={previewHtml}
            {...testIdProps(testIds.documents.previewFrame)}
          />
        </div>
      ) : null}
    </section>
  );
}
