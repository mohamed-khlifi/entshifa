"use client";

import type { ReactNode } from "react";

import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils/cn";

export type TableToolbarFieldProps = {
  label: string;
  htmlFor?: string;
  className?: string;
  children: ReactNode;
};

/** Label-above control shell for data-table search and filter rows. */
export function TableToolbarField({
  label,
  htmlFor,
  className,
  children,
}: TableToolbarFieldProps) {
  return (
    <div className={cn("flex min-w-[9rem] flex-col gap-1.5", className)}>
      <Label
        htmlFor={htmlFor}
        className="text-xs font-medium tracking-wide text-muted-foreground"
      >
        {label}
      </Label>
      {children}
    </div>
  );
}
