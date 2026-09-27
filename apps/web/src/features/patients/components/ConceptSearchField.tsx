"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import { useConceptSearchQuery } from "../hooks/use-patient-queries";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fieldTestId } from "@/lib/forms/field-test-id";
import { testIdProps } from "@/lib/test/test-id";

const SEARCH_DEBOUNCE_MS = 300;

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
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const search = useConceptSearchQuery(debouncedQuery);
  const inputId = fieldTestId(name);
  const listId = fieldTestId(`${name}Results`);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setDebouncedQuery(query.trim());
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(handle);
  }, [query]);

  const showPanel =
    debouncedQuery.length >= 2 &&
    (search.isFetching ||
      (search.data !== undefined && search.data.items.length === 0) ||
      (search.data !== undefined && search.data.items.length > 0));

  return (
    <div className="space-y-1.5">
      <Label htmlFor={inputId}>{label}</Label>
      {selectedId ? (
        <p className="text-sm text-foreground">{selectedDisplay}</p>
      ) : null}
      <div className="relative">
        <Input
          id={inputId}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t("concept.placeholder")}
          autoComplete="off"
          {...testIdProps(inputId)}
        />
        {showPanel ? (
          <div
            className="absolute left-0 right-0 top-full z-20 mt-1 overflow-hidden rounded-lg border border-border bg-popover shadow-md"
            {...testIdProps(listId)}
          >
            {search.isFetching ? (
              <p className="px-3 py-2 text-xs text-muted-foreground">
                {t("concept.searching")}
              </p>
            ) : null}
            {!search.isFetching &&
            search.data &&
            search.data.items.length === 0 ? (
              <p className="px-3 py-2 text-xs text-muted-foreground">
                {t("concept.empty")}
              </p>
            ) : null}
            {!search.isFetching &&
            search.data &&
            search.data.items.length > 0 ? (
              <ul className="max-h-40 overflow-auto">
                {search.data.items.map((item) => (
                  <li key={item.publicId}>
                    <button
                      type="button"
                      className="w-full px-3 py-2 text-start text-sm hover:bg-accent"
                      onClick={() => {
                        onSelect({
                          publicId: item.publicId,
                          display: item.display,
                        });
                        setQuery("");
                        setDebouncedQuery("");
                      }}
                    >
                      {item.display}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
