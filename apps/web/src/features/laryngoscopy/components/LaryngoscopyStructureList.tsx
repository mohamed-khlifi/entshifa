"use client";

import { useTranslations } from "next-intl";

import {
  ABNORMAL_FINDINGS,
  STRUCTURE_STATUSES,
  type LaryngoscopyDraft,
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
  laryngoscopyStructureControlTestId,
  laryngoscopyStructureTestId,
  testIdProps,
} from "@/lib/test/test-id";

type LaryngoscopyStructureListProps = {
  draft: LaryngoscopyDraft;
  regions: readonly MapRegionDefinition[];
  findings: readonly ResolvedConcept[];
  readOnly: boolean;
  onChange: (draft: LaryngoscopyDraft) => void;
  onFocus: (regionId: string, laterality: StructureLaterality) => void;
};

export function LaryngoscopyStructureList({
  draft,
  regions,
  findings,
  readOnly,
  onChange,
  onFocus,
}: LaryngoscopyStructureListProps) {
  const t = useTranslations("laryngoscopy");
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
                laryngoscopyStructureTestId(row.bodySiteCode, row.laterality),
              )}
            >
              <button
                type="button"
                className="text-start text-sm font-medium"
                onClick={() => region && onFocus(region.id, row.laterality)}
                {...testIdProps(
                  laryngoscopyStructureControlTestId(
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
              <label className="space-y-1 text-xs">
                {t("structures.status")}
                <select
                  className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                  disabled={readOnly}
                  value={row.status}
                  onChange={(event) =>
                    onChange(
                      withStructureStatus(
                        draft,
                        row.bodySiteCode,
                        row.laterality,
                        event.target.value as StructureStatus,
                      ),
                    )
                  }
                  {...testIdProps(
                    laryngoscopyStructureControlTestId(
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
              <label className="space-y-1 text-xs">
                {t("structures.finding")}
                <select
                  className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                  disabled={readOnly || row.status !== "abnormal"}
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
                    laryngoscopyStructureControlTestId(
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
            </li>
          );
        })}
      </ul>
    </section>
  );
}
