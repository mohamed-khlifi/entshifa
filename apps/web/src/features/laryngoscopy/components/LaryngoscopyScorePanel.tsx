"use client";

import { useTranslations } from "next-intl";

import {
  GRBAS_CHOICES,
  GRBAS_ITEMS,
  PAS_MAX,
  PAS_MIN,
  RFS_CHOICES,
  RFS_ITEMS,
  type GrbasItem,
  type LaryngoscopyDraft,
} from "../lib/draft";
import { grbasItemLabel, rfsItemLabel, scoreCodeLabel } from "../lib/labels";
import type {
  LaryngoscopyExamRead,
  ResolvedConcept,
} from "@/lib/api/generated";
import {
  laryngoscopyGrbasTestId,
  laryngoscopyRfsTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

type LaryngoscopyScorePanelProps = {
  draft: LaryngoscopyDraft;
  saved: LaryngoscopyExamRead | null;
  consistencies: readonly ResolvedConcept[];
  residueSites: readonly ResolvedConcept[];
  readOnly: boolean;
  onChange: (draft: LaryngoscopyDraft) => void;
};

export function LaryngoscopyScorePanel({
  draft,
  saved,
  consistencies,
  residueSites,
  readOnly,
  onChange,
}: LaryngoscopyScorePanelProps) {
  const t = useTranslations("laryngoscopy");
  return (
    <section
      className="space-y-4"
      {...testIdProps(testIds.laryngoscopy.scores)}
    >
      <h3 className="text-sm font-semibold">{t("scores.title")}</h3>
      {saved ? (
        <ul className="text-sm text-muted-foreground">
          {saved.scores.map((stamp) => (
            <li key={stamp.code}>
              {scoreCodeLabel(t, stamp.code)} {t("scores.total")}: {stamp.value}
            </li>
          ))}
        </ul>
      ) : (
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.laryngoscopy.scorePending)}
        >
          {t("scores.pending")}
        </p>
      )}
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          disabled={readOnly}
          checked={draft.includeRfs}
          onChange={(event) =>
            onChange({ ...draft, includeRfs: event.target.checked })
          }
          {...testIdProps(testIds.laryngoscopy.rfsToggle)}
        />
        {t("scores.includeRfs")}
      </label>
      {draft.includeRfs ? (
        <div className="grid gap-2 sm:grid-cols-2">
          {RFS_ITEMS.map((item) => (
            <label key={item} className="space-y-1 text-sm">
              {rfsItemLabel(t, item)}
              <select
                className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                disabled={readOnly}
                value={draft.rfs[item] ?? ""}
                onChange={(event) =>
                  onChange({
                    ...draft,
                    rfs: {
                      ...draft.rfs,
                      [item]:
                        event.target.value === ""
                          ? null
                          : Number.parseInt(event.target.value, 10),
                    },
                  })
                }
                {...testIdProps(laryngoscopyRfsTestId(item))}
              >
                <option value="">{t("status.unset")}</option>
                {RFS_CHOICES[item].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
      ) : null}
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          disabled={readOnly}
          checked={draft.includeGrbas}
          onChange={(event) =>
            onChange({ ...draft, includeGrbas: event.target.checked })
          }
          {...testIdProps(testIds.laryngoscopy.grbasToggle)}
        />
        {t("scores.includeGrbas")}
      </label>
      {draft.includeGrbas ? (
        <div className="grid gap-2 sm:grid-cols-5">
          {GRBAS_ITEMS.map((item: GrbasItem) => (
            <label key={item} className="space-y-1 text-sm">
              {grbasItemLabel(t, item)}
              <select
                className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                disabled={readOnly}
                value={draft.grbas[item] ?? ""}
                onChange={(event) =>
                  onChange({
                    ...draft,
                    grbas: {
                      ...draft.grbas,
                      [item]:
                        event.target.value === ""
                          ? null
                          : Number.parseInt(event.target.value, 10),
                    },
                  })
                }
                {...testIdProps(laryngoscopyGrbasTestId(item))}
              >
                <option value="">{t("status.unset")}</option>
                {GRBAS_CHOICES.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
      ) : null}
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          disabled={readOnly}
          checked={draft.includeFees}
          onChange={(event) =>
            onChange({ ...draft, includeFees: event.target.checked })
          }
          {...testIdProps(testIds.laryngoscopy.feesToggle)}
        />
        {t("scores.includeFees")}
      </label>
      {draft.includeFees ? (
        <div className="space-y-3">
          <h4 className="text-sm font-medium">{t("fees.title")}</h4>
          <label className="space-y-1 text-sm">
            {t("scores.pas")}
            <input
              type="number"
              min={PAS_MIN}
              max={PAS_MAX}
              className="flex h-10 w-full rounded-lg border border-input bg-card px-3 text-sm"
              disabled={readOnly}
              value={draft.pasScore ?? ""}
              onChange={(event) =>
                onChange({
                  ...draft,
                  pasScore:
                    event.target.value === ""
                      ? null
                      : Number.parseInt(event.target.value, 10),
                })
              }
              {...testIdProps(testIds.laryngoscopy.pas)}
            />
          </label>
          <fieldset className="space-y-1">
            <legend className="text-sm">{t("fees.consistencies")}</legend>
            {consistencies.map((item) => (
              <label
                key={item.code}
                className="flex items-center gap-2 text-sm"
              >
                <input
                  type="checkbox"
                  disabled={readOnly}
                  checked={draft.consistencies.includes(item.code)}
                  onChange={(event) => {
                    const next = event.target.checked
                      ? [...draft.consistencies, item.code]
                      : draft.consistencies.filter(
                          (code) => code !== item.code,
                        );
                    onChange({ ...draft, consistencies: next });
                  }}
                />
                {item.display}
              </label>
            ))}
          </fieldset>
          <fieldset className="space-y-1">
            <legend className="text-sm">{t("fees.residue")}</legend>
            {residueSites.map((item) => (
              <label
                key={item.code}
                className="flex items-center gap-2 text-sm"
              >
                <input
                  type="checkbox"
                  disabled={readOnly}
                  checked={draft.residueSiteCodes.includes(item.code)}
                  onChange={(event) => {
                    const next = event.target.checked
                      ? [...draft.residueSiteCodes, item.code]
                      : draft.residueSiteCodes.filter(
                          (code) => code !== item.code,
                        );
                    onChange({ ...draft, residueSiteCodes: next });
                  }}
                />
                {item.display}
              </label>
            ))}
          </fieldset>
        </div>
      ) : null}
    </section>
  );
}
