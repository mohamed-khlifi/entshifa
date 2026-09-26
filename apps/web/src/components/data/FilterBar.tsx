"use client";

import { Search } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState, type ReactNode } from "react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils/cn";
import { testIdProps, testIds } from "@/lib/test/test-id";

export type FilterBarProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  trailing?: ReactNode;
  debounceMs?: number;
};

export function FilterBar({
  value,
  onChange,
  placeholder,
  className,
  trailing,
  debounceMs = 300,
}: FilterBarProps) {
  const t = useTranslations("data");
  const [local, setLocal] = useState(value);

  useEffect(() => {
    setLocal(value);
  }, [value]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (local !== value) {
        onChange(local);
      }
    }, debounceMs);
    return () => clearTimeout(timer);
  }, [debounceMs, local, onChange, value]);

  return (
    <div
      className={cn("flex flex-wrap items-center gap-3", className)}
      {...testIdProps(testIds.data.filterBar)}
    >
      <div className="relative min-w-[12rem] flex-1">
        <Search
          className="pointer-events-none absolute start-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden
        />
        <Input
          type="search"
          value={local}
          onChange={(event) => setLocal(event.target.value)}
          placeholder={placeholder ?? t("filter.placeholder")}
          className="ps-9"
          aria-label={t("filter.label")}
          {...testIdProps(testIds.data.filterInput)}
        />
      </div>
      {trailing}
    </div>
  );
}
