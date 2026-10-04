"use client";

import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  encounterSuggestionTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

import {
  documentLabel,
  examSectionLabel,
  instrumentLabel,
  testLabel,
} from "../lib/suggestion-labels";
import type { PlanKind } from "../lib/plan-items";

type SuggestionPanelProps = {
  tests: readonly string[];
  instruments: readonly string[];
  documents: readonly string[];
  pendingSections: readonly string[];
  selectedSources: ReadonlySet<string>;
  disabled: boolean;
  followUpDays: number | null;
  onToggle: (source: string, kind: PlanKind, detail: string) => void;
  onFollowUp: () => void;
};

export function SuggestionPanel({
  tests,
  instruments,
  documents,
  pendingSections,
  selectedSources,
  disabled,
  followUpDays,
  onToggle,
  onFollowUp,
}: SuggestionPanelProps) {
  const t = useTranslations("encounters");
  if (
    tests.length === 0 &&
    instruments.length === 0 &&
    documents.length === 0 &&
    pendingSections.length === 0 &&
    followUpDays === null
  ) {
    return null;
  }

  return (
    <section
      className="space-y-3"
      {...testIdProps(testIds.encounters.suggestions)}
    >
      <h2 className="text-lg font-semibold">{t("suggestions.title")}</h2>
      <SuggestionGroup
        title={t("suggestions.testsTitle")}
        kind="test"
        planKind="test_requested"
        codes={tests}
        labelFor={(code) => testLabel(t, code)}
        selectedSources={selectedSources}
        disabled={disabled}
        onToggle={onToggle}
      />
      <SuggestionGroup
        title={t("suggestions.instrumentsTitle")}
        kind="instrument"
        planKind="test_requested"
        codes={instruments}
        labelFor={(code) => instrumentLabel(t, code)}
        selectedSources={selectedSources}
        disabled={disabled}
        onToggle={onToggle}
      />
      <SuggestionGroup
        title={t("suggestions.documentsTitle")}
        kind="document"
        planKind="advice"
        codes={documents}
        labelFor={(code) => documentLabel(t, code)}
        selectedSources={selectedSources}
        disabled={disabled}
        onToggle={onToggle}
      />
      {pendingSections.length > 0 ? (
        <div className="space-y-1">
          <h3 className="text-sm font-medium">
            {t("suggestions.sectionsTitle")}
          </h3>
          <ul className="space-y-1 text-sm text-muted-foreground">
            {pendingSections.map((section) => (
              <li key={section}>{examSectionLabel(t, section)}</li>
            ))}
          </ul>
          <p className="text-sm text-muted-foreground">
            {t("suggestions.pending")}
          </p>
        </div>
      ) : null}
      {followUpDays !== null ? (
        <Button
          type="button"
          variant="secondary"
          disabled={disabled}
          onClick={onFollowUp}
          {...testIdProps(testIds.encounters.followUp)}
        >
          {t("plan.addFollowUp", { days: followUpDays })}
        </Button>
      ) : null}
    </section>
  );
}

function SuggestionGroup({
  title,
  kind,
  planKind,
  codes,
  labelFor,
  selectedSources,
  disabled,
  onToggle,
}: {
  title: string;
  kind: string;
  planKind: PlanKind;
  codes: readonly string[];
  labelFor: (code: string) => string;
  selectedSources: ReadonlySet<string>;
  disabled: boolean;
  onToggle: (source: string, kind: PlanKind, detail: string) => void;
}) {
  if (codes.length === 0) {
    return null;
  }
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium">{title}</h3>
      <div className="flex flex-wrap gap-2">
        {codes.map((code) => {
          const source = `${kind}:${code}`;
          const label = labelFor(code);
          const pressed = selectedSources.has(source);
          return (
            <Button
              key={source}
              type="button"
              variant={pressed ? "default" : "secondary"}
              disabled={disabled}
              aria-pressed={pressed}
              onClick={() => onToggle(source, planKind, label)}
              {...testIdProps(encounterSuggestionTestId(kind, code))}
            >
              {label}
            </Button>
          );
        })}
      </div>
    </div>
  );
}
