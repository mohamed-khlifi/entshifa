"use client";

import { useTranslations } from "next-intl";

import type { DrugRead, FormularyEntryRead } from "@/lib/api/generated";
import {
  prescriptionFormularyTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

type DrugSearchProps = {
  query: string;
  onQueryChange: (value: string) => void;
  formulary: readonly FormularyEntryRead[];
  catalog: readonly DrugRead[];
  onPickFormulary: (entry: FormularyEntryRead) => void;
  onPickCatalog: (drug: DrugRead) => void;
};

export function DrugSearch({
  query,
  onQueryChange,
  formulary,
  catalog,
  onPickFormulary,
  onPickCatalog,
}: DrugSearchProps) {
  const t = useTranslations("prescriptions");
  const showEmpty =
    query.trim().length > 0 && formulary.length === 0 && catalog.length === 0;

  return (
    <div className="space-y-3">
      <label className="block space-y-1 text-sm font-medium">
        {t("builder.search")}
        <input
          type="search"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          className="mt-1 flex h-11 w-full rounded-lg border border-input bg-card px-3 text-sm"
          {...testIdProps(testIds.prescriptions.search)}
        />
      </label>
      {showEmpty ? (
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.prescriptions.searchEmpty)}
        >
          {t("builder.searchEmpty")}
        </p>
      ) : null}
      {formulary.length > 0 ? (
        <div className="space-y-2">
          <h3
            className="text-sm font-semibold"
            {...testIdProps(testIds.prescriptions.formularyHeading)}
          >
            {t("builder.formularyHeading")}
          </h3>
          <ul className="space-y-1">
            {formulary.map((entry) => (
              <li key={entry.publicId}>
                <button
                  type="button"
                  className="w-full rounded-lg border border-border px-3 py-2 text-start text-sm hover:bg-muted"
                  onClick={() => onPickFormulary(entry)}
                  {...testIdProps(prescriptionFormularyTestId(entry.publicId))}
                >
                  <span className="font-medium">{entry.brandName}</span>
                  <span className="text-muted-foreground">
                    {" "}
                    {entry.drug.concept?.display ?? entry.drug.innName}
                  </span>
                  {entry.drug.isOtotoxic ? (
                    <span className="ms-2 text-destructive">
                      {t("tags.ototoxic")}
                    </span>
                  ) : null}
                  {entry.drug.isAnticoagulant ? (
                    <span className="ms-2">{t("tags.anticoagulant")}</span>
                  ) : null}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {catalog.length > 0 ? (
        <div className="space-y-2">
          <h3
            className="text-sm font-semibold"
            {...testIdProps(testIds.prescriptions.catalogHeading)}
          >
            {t("builder.catalogHeading")}
          </h3>
          <ul className="space-y-1">
            {catalog.map((drug) => (
              <li key={drug.publicId}>
                <button
                  type="button"
                  className="w-full rounded-lg border border-dashed border-border px-3 py-2 text-start text-sm hover:bg-muted"
                  onClick={() => onPickCatalog(drug)}
                >
                  {drug.concept?.display ?? drug.innName}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
