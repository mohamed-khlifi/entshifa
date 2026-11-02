"use client";

import { useLocale, useTranslations } from "next-intl";

import type { OverlaySeries } from "../types/audiology.types";
import { formatDate } from "@/lib/i18n/format";
import {
  audiogramOverlayToggleTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

type ComparisonOverlayProps = {
  overlays: OverlaySeries[];
  selectedIds: ReadonlySet<string>;
  onToggle: (publicId: string) => void;
};

export function ComparisonOverlay({
  overlays,
  selectedIds,
  onToggle,
}: ComparisonOverlayProps) {
  const t = useTranslations("audiology");
  const locale = useLocale();

  if (overlays.length === 0) {
    return null;
  }

  return (
    <section
      className="space-y-2"
      {...testIdProps(testIds.audiology.overlayList)}
    >
      <h3 className="text-sm font-semibold">{t("overlay.title")}</h3>
      <ul className="flex flex-wrap gap-2">
        {overlays.map((row) => {
          const active = selectedIds.has(row.publicId);
          return (
            <li key={row.publicId}>
              <button
                type="button"
                className={`rounded-full border px-3 py-1 text-sm ${
                  active
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground"
                }`}
                onClick={() => onToggle(row.publicId)}
                {...testIdProps(audiogramOverlayToggleTestId(row.publicId))}
              >
                {formatDate(row.performedAt, locale)}
                {row.isBaseline ? ` · ${t("overlay.baseline")}` : ""}
              </button>
            </li>
          );
        })}
      </ul>
      {selectedIds.size > 0 ? (
        <p
          className="text-xs text-muted-foreground"
          {...testIdProps(testIds.audiology.overlayLegend)}
        >
          {t("overlay.legend")}
        </p>
      ) : null}
    </section>
  );
}
