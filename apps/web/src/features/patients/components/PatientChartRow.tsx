"use client";

import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { testIdProps } from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

export type ChartBadgeTone = "neutral" | "success" | "warning" | "danger";

const badgeToneClass: Record<ChartBadgeTone, string> = {
  neutral: "bg-muted text-muted-foreground ring-1 ring-inset ring-border/80",
  success:
    "bg-emerald-500/12 text-emerald-800 ring-1 ring-inset ring-emerald-500/25 dark:text-emerald-300",
  warning:
    "bg-amber-500/12 text-amber-900 ring-1 ring-inset ring-amber-500/30 dark:text-amber-200",
  danger:
    "bg-destructive/12 text-destructive ring-1 ring-inset ring-destructive/35",
};

export function ChartBadge({
  tone = "neutral",
  children,
}: {
  tone?: ChartBadgeTone;
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold tracking-tight",
        badgeToneClass[tone],
      )}
    >
      {children}
    </span>
  );
}

type PatientChartRowProps = {
  title: ReactNode;
  badges?: ReactNode;
  canWrite: boolean;
  removeLabel: string;
  removeTestId: string;
  onRemove: () => void;
};

export function PatientChartRow({
  title,
  badges,
  canWrite,
  removeLabel,
  removeTestId,
  onRemove,
}: PatientChartRowProps) {
  return (
    <li className="flex flex-col gap-3 rounded-xl border border-border/70 bg-gradient-to-br from-muted/50 to-muted/25 px-3 py-3 shadow-sm sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0 flex-1 space-y-2">
        <p className="text-sm font-medium leading-snug text-foreground">
          {title}
        </p>
        {badges ? (
          <div className="flex flex-wrap items-center gap-1.5">{badges}</div>
        ) : null}
      </div>
      {canWrite ? (
        <Button
          type="button"
          size="sm"
          variant="secondary"
          className="shrink-0 border border-border/80 bg-background/80"
          onClick={onRemove}
          {...testIdProps(removeTestId)}
        >
          {removeLabel}
        </Button>
      ) : null}
    </li>
  );
}
