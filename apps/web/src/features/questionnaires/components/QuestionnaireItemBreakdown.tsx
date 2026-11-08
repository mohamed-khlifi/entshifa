"use client";

import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";

import type { QuestionnaireResponseItemDetailRead } from "@/lib/api/generated";
import {
  testIdProps,
  testIds,
  questionnaireItemRowTestId,
} from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

import { subscaleLabel } from "../lib/labels";

type QuestionnaireItemBreakdownProps = {
  items: readonly QuestionnaireResponseItemDetailRead[];
};

export function QuestionnaireItemBreakdown({
  items,
}: QuestionnaireItemBreakdownProps) {
  const t = useTranslations("questionnaires");
  const subscales = useMemo(() => {
    const set = new Set<string>();
    for (const item of items) {
      if (item.subscale) {
        set.add(item.subscale);
      }
    }
    return [...set].sort();
  }, [items]);
  const [filter, setFilter] = useState<string>("");

  const visible = useMemo(() => {
    const sorted = [...items].sort((a, b) => a.position - b.position);
    if (!filter) {
      return sorted;
    }
    return sorted.filter((row) => row.subscale === filter);
  }, [filter, items]);

  if (items.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        {t("presentation.itemsEmpty")}
      </p>
    );
  }

  return (
    <section
      className="space-y-3"
      {...testIdProps(testIds.questionnaires.itemBreakdown)}
    >
      <h3 className="text-sm font-semibold">
        {t("presentation.itemsTitle")}{" "}
        <span className="text-muted-foreground">({items.length})</span>
      </h3>
      {subscales.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          <FilterChip
            active={filter === ""}
            label={t("presentation.itemsFilterAll")}
            onClick={() => setFilter("")}
            testId={testIds.questionnaires.itemSubscaleFilter}
          />
          {subscales.map((code) => (
            <FilterChip
              key={code}
              active={filter === code}
              label={subscaleLabel(t, code)}
              onClick={() => setFilter(code)}
              testId={testIds.questionnaires.itemSubscaleFilter}
            />
          ))}
        </div>
      ) : null}
      <ul className="space-y-2">
        {visible.map((item) => {
          const span = Math.max(item.maxValue - item.minValue, 1);
          const ratio = (item.value - item.minValue) / span;
          return (
            <li
              key={item.code}
              className="rounded-lg border px-3 py-2"
              {...testIdProps(questionnaireItemRowTestId(item.code))}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-muted-foreground">
                    {item.position}.{" "}
                    {item.subscale ? subscaleLabel(t, item.subscale) : null}
                  </p>
                  <p className="text-sm font-medium leading-snug">
                    {item.text}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {item.optionText}
                  </p>
                </div>
                <span className="text-sm font-semibold tabular-nums">
                  {item.value}/{item.maxValue}
                </span>
              </div>
              <div
                className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted"
                aria-hidden
              >
                <div
                  className={cn(
                    "h-full rounded-full",
                    ratio >= 0.6 ? "bg-primary" : "bg-primary/60",
                  )}
                  style={{ width: `${Math.min(100, ratio * 100)}%` }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function FilterChip({
  active,
  label,
  onClick,
  testId,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
  testId: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full px-3 py-1 text-xs font-medium",
        active
          ? "bg-primary/10 text-primary"
          : "bg-muted text-muted-foreground",
      )}
      {...testIdProps(testId)}
    >
      {label}
    </button>
  );
}
