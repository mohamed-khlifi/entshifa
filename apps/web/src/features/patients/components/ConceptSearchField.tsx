"use client";

import { useEffect, useId, useState } from "react";
import { useTranslations } from "next-intl";

import {
  useConceptPickerOptions,
  type ConceptPickerParams,
} from "../hooks/use-patient-queries";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { conceptOptionTestId, fieldTestId } from "@/lib/forms/field-test-id";
import { testIdProps } from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

const SEARCH_DEBOUNCE_MS = 300;

type ConceptSearchFieldProps = {
  name: string;
  label: string;
  selectedId: string;
  selectedDisplay: string;
  kind?: string;
  kinds?: string[];
  valueSetCode?: string;
  className?: string;
  onSelect: (concept: { publicId: string; display: string }) => void;
  onClear?: () => void;
};

export function ConceptSearchField({
  name,
  label,
  selectedId,
  selectedDisplay,
  kind,
  kinds,
  valueSetCode,
  className,
  onSelect,
  onClear,
}: ConceptSearchFieldProps) {
  const t = useTranslations("patients");
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const pickerParams: ConceptPickerParams = {
    kind,
    kinds,
    valueSetCode,
  };
  const { items, isFetching } = useConceptPickerOptions(
    debouncedQuery,
    pickerParams,
  );
  const inputId = fieldTestId(name);
  const listId = fieldTestId(`${name}Results`);
  const panelId = useId();

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setDebouncedQuery(query.trim());
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(handle);
  }, [query]);

  const showResults =
    isOpen && (isFetching || items.length > 0 || debouncedQuery.length > 0);

  return (
    <div className={cn("space-y-1.5", className)}>
      <Label htmlFor={inputId}>{label}</Label>
      {selectedId ? (
        <div
          className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-muted/40 px-3 py-2"
          {...testIdProps(fieldTestId(`${name}Selected`))}
        >
          <span className="text-sm font-medium leading-snug text-foreground">
            {selectedDisplay}
          </span>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => {
              onClear?.();
              setQuery("");
              setDebouncedQuery("");
              setIsOpen(true);
            }}
            {...testIdProps(fieldTestId(`${name}Change`))}
          >
            {t("concept.change")}
          </Button>
        </div>
      ) : (
        <>
          <Input
            id={inputId}
            value={query}
            onFocus={() => setIsOpen(true)}
            onBlur={() => setIsOpen(false)}
            onChange={(event) => {
              setQuery(event.target.value);
              setIsOpen(true);
            }}
            placeholder={t("concept.placeholder")}
            autoComplete="off"
            role="combobox"
            aria-expanded={showResults}
            aria-controls={panelId}
            aria-autocomplete="list"
            {...testIdProps(inputId)}
          />
          {showResults ? (
            <div
              id={panelId}
              className="rounded-lg border border-border bg-card shadow-sm"
              {...testIdProps(listId)}
            >
              {isFetching ? (
                <p className="px-3 py-2 text-sm text-muted-foreground">
                  {t("concept.searching")}
                </p>
              ) : null}
              {!isFetching && items.length === 0 ? (
                <p className="px-3 py-2 text-sm text-muted-foreground">
                  {t("concept.empty")}
                </p>
              ) : null}
              {!isFetching && items.length > 0 ? (
                <ul
                  className="max-h-48 divide-y divide-border overflow-auto"
                  role="listbox"
                >
                  {items.map((item) => (
                    <li key={item.publicId}>
                      <button
                        type="button"
                        role="option"
                        aria-selected={selectedId === item.publicId}
                        className="w-full px-3 py-2.5 text-start text-sm hover:bg-accent focus-visible:bg-accent focus-visible:outline-none"
                        onMouseDown={(event) => event.preventDefault()}
                        onClick={() => {
                          onSelect({
                            publicId: item.publicId,
                            display: item.display,
                          });
                          setQuery("");
                          setDebouncedQuery("");
                          setIsOpen(false);
                        }}
                        {...testIdProps(
                          conceptOptionTestId(name, item.publicId),
                        )}
                      >
                        {item.display}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
