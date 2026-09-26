"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { useConceptSearchQuery } from "../hooks/use-patient-queries";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fieldTestId } from "@/lib/forms/field-test-id";
import { testIdProps } from "@/lib/test/test-id";

type ConceptSearchFieldProps = {
  name: string;
  label: string;
  selectedId: string;
  selectedDisplay: string;
  onSelect: (concept: { publicId: string; display: string }) => void;
};

export function ConceptSearchField({
  name,
  label,
  selectedId,
  selectedDisplay,
  onSelect,
}: ConceptSearchFieldProps) {
  const t = useTranslations("patients");
  const [query, setQuery] = useState("");
  const search = useConceptSearchQuery(query);
  const inputId = fieldTestId(name);
  const listId = fieldTestId(`${name}Results`);

  return (
    <div className="space-y-2">
      <Label htmlFor={inputId}>{label}</Label>
      {selectedId ? (
        <p className="text-sm text-foreground">{selectedDisplay}</p>
      ) : null}
      <Input
        id={inputId}
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder={t("concept.placeholder")}
        {...testIdProps(inputId)}
      />
      {search.isFetching ? (
        <p className="text-xs text-muted-foreground">
          {t("concept.searching")}
        </p>
      ) : null}
      {search.data &&
      search.data.items.length === 0 &&
      query.trim().length >= 2 ? (
        <p className="text-xs text-muted-foreground">{t("concept.empty")}</p>
      ) : null}
      {search.data && search.data.items.length > 0 ? (
        <ul
          className="max-h-40 overflow-auto rounded-lg border border-border"
          {...testIdProps(listId)}
        >
          {search.data.items.map((item) => (
            <li key={item.publicId}>
              <button
                type="button"
                className="w-full px-3 py-2 text-start text-sm hover:bg-accent"
                onClick={() => {
                  onSelect({ publicId: item.publicId, display: item.display });
                  setQuery("");
                }}
              >
                {item.display}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
