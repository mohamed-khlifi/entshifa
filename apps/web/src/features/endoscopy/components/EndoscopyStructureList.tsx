"use client";

import { useTranslations } from "next-intl";

import {
  ABNORMAL_FINDINGS,
  STRUCTURE_STATUSES,
  type EndoscopyDraft,
  type StructureLaterality,
  type StructureStatus,
  withStructureFinding,
  withStructureStatus,
} from "../lib/draft";
import { lateralityLabel, structureStatusLabel } from "../lib/labels";
import { examinationRegionLabel } from "@/lib/anatomy/region-labels";
import type { MapRegionDefinition } from "@/lib/anatomy/types";
import type { ResolvedConcept } from "@/lib/api/generated";
import {
  endoscopyStructureControlTestId,
  endoscopyStructureTestId,
  testIdProps,
} from "@/lib/test/test-id";

type EndoscopyStructureListProps = {
  draft: EndoscopyDraft;
  regions: readonly MapRegionDefinition[];
  findings: readonly ResolvedConcept[];
  readOnly: boolean;
  onChange: (draft: EndoscopyDraft) => void;
  onFocus: (regionId: string, laterality: StructureLaterality) => void;
};

export function EndoscopyStructureList({
  draft,
  regions,
  findings,
  readOnly,
  onChange,
  onFocus,
}: EndoscopyStructureListProps) {
  const t = useTranslations("endoscopy");
  const tExam = useTranslations("examination");
  const abnormal = findings.filter((finding) =>
    (ABNORMAL_FINDINGS as readonly string[]).includes(finding.code),
  );

  return (
    <section className="space-y-3">
      <h3 className="text-sm font-semibold">{t("structures.title")}</h3>
      <ul className="space-y-2">
        {draft.structures.map((row) => {
          const region = regions.find(
            (item) => item.bodySiteCode === row.bodySiteCode,
          );
          const label = region
            ? examinationRegionLabel(tExam, region.labelKey)
            : t("structures.title");
          return (
            <li
              key={`${row.laterality}:${row.bodySiteCode}`}
              className="grid gap-2 rounded-xl border border-border bg-card p-3 sm:grid-cols-[minmax(0,1.4fr)_auto_minmax(0,1fr)] sm:items-end"
              {...testIdProps(
                endoscopyStructureTestId(row.bodySiteCode, row.laterality),
              )}
            >
              <button
                type="button"
                className="text-start text-sm font-medium"
                onClick={() => region && onFocus(region.id, row.laterality)}
                {...testIdProps(
                  endoscopyStructureControlTestId(
                    row.bodySiteCode,
                    row.laterality,
                    "focus",
                  ),
                )}
              >
                {label}
                <span className="ms-2 text-xs font-normal text-muted-foreground">
                  {lateralityLabel(t, row.laterality)}
                </span>
              </button>
              <label className="space-y-1 text-xs text-muted-foreground">
                {t("structures.status")}
                <select
                  className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm text-foreground"
                  disabled={readOnly}
                  value={row.status}
                  onChange={(event) => {
                    const status = event.target.value as StructureStatus;
                    onChange(
                      withStructureStatus(
                        draft,
                        row.bodySiteCode,
                        row.laterality,
                        status,
                      ),
                    );
                  }}
                  {...testIdProps(
                    endoscopyStructureControlTestId(
                      row.bodySiteCode,
                      row.laterality,
                      "status",
                    ),
                  )}
                >
                  {STRUCTURE_STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {structureStatusLabel(t, status)}
                    </option>
                  ))}
                </select>
              </label>
              {row.status === "abnormal" ? (
                <label className="space-y-1 text-xs text-muted-foreground">
                  {t("structures.finding")}
                  <select
                    className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm text-foreground"
                    disabled={readOnly}
                    value={row.findingCode ?? ""}
                    onChange={(event) =>
                      onChange(
                        withStructureFinding(
                          draft,
                          row.bodySiteCode,
                          row.laterality,
                          event.target.value,
                        ),
                      )
                    }
                    {...testIdProps(
                      endoscopyStructureControlTestId(
                        row.bodySiteCode,
                        row.laterality,
                        "finding",
                      ),
                    )}
                  >
                    <option value="">{t("structures.findingEmpty")}</option>
                    {abnormal.map((finding) => (
                      <option key={finding.code} value={finding.code}>
                        {finding.display}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
