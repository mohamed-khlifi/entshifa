"use client";

import type { ReactNode } from "react";

import { Label } from "@/components/ui/label";
import { fieldErrorTestId } from "@/lib/forms/field-test-id";
import { cn } from "@/lib/utils/cn";
import { testIdProps } from "@/lib/test/test-id";

export type FormFieldShellProps = {
  name: string;
  label: string;
  description?: string;
  required?: boolean;
  unit?: string;
  error?: string;
  children: ReactNode;
  className?: string;
  htmlFor: string;
};

export function FormFieldShell({
  name,
  label,
  description,
  required = false,
  unit,
  error,
  children,
  className,
  htmlFor,
}: FormFieldShellProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-baseline justify-between gap-2">
        <Label htmlFor={htmlFor} className="text-sm font-medium">
          {label}
          {required ? (
            <span className="ms-1 text-destructive" aria-hidden>
              *
            </span>
          ) : null}
        </Label>
        {unit ? (
          <span className="text-xs font-medium text-muted-foreground">
            {unit}
          </span>
        ) : null}
      </div>
      {description ? (
        <p className="text-xs text-muted-foreground">{description}</p>
      ) : null}
      {children}
      {error ? (
        <p
          className="text-sm text-destructive"
          role="alert"
          {...testIdProps(fieldErrorTestId(name))}
        >
          {error}
        </p>
      ) : null}
    </div>
  );
}
