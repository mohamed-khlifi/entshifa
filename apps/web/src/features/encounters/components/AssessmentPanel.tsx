"use client";

import { useTranslations } from "next-intl";

import { TextAreaField } from "@/components/forms/TextAreaField";
import { Button } from "@/components/ui/button";
import { ConceptSearchField } from "@/features/patients";
import {
  diagnosisFavoriteTestId,
  diagnosisRowTestId,
  diagnosisSaveFavoriteTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

import {
  clinicianDiagnosis,
  type DiagnosisDraft,
  type DiagnosisLaterality,
  type DiagnosisStatus,
} from "../lib/cockpit-state";
import { diagnosisSideLabel, diagnosisStatusLabel } from "../lib/labels";

const SIDES: DiagnosisLaterality[] = ["right", "left", "bilateral", "na"];
const STATUSES: DiagnosisStatus[] = ["suspected", "confirmed", "ruled_out"];

export type DiagnosisFavoriteChip = {
  conceptPublicId: string;
  display: string;
};

type AssessmentPanelProps = {
  rows: readonly DiagnosisDraft[];
  favorites: readonly string[];
  doctorFavorites: readonly DiagnosisFavoriteChip[];
  disabled: boolean;
  onAdd: (row: DiagnosisDraft) => void;
  onChange: (
    conceptPublicId: string,
    laterality: DiagnosisLaterality,
    patch: Partial<Pick<DiagnosisDraft, "laterality" | "status">>,
  ) => void;
  onRemove: (conceptPublicId: string, laterality: DiagnosisLaterality) => void;
  onPromote: (row: DiagnosisDraft) => void;
  onFavorite: (code: string) => void;
  onSaveFavorite: (row: DiagnosisDraft) => void;
};

export function AssessmentPanel({
  rows,
  favorites,
  doctorFavorites,
  disabled,
  onAdd,
  onChange,
  onRemove,
  onPromote,
  onFavorite,
  onSaveFavorite,
}: AssessmentPanelProps) {
  const t = useTranslations("encounters");
  return (
    <section
      className="space-y-3"
      {...testIdProps(testIds.encounters.assessment)}
    >
      <h2 className="text-lg font-semibold">{t("assessment.title")}</h2>
      <ConceptSearchField
        name="encounterDiagnosis"
        label={t("assessment.search")}
        selectedId=""
        selectedDisplay=""
        kind="diagnosis"
        valueSetCode="ent.diagnoses"
        onSelect={(concept) =>
          onAdd(clinicianDiagnosis(concept.publicId, concept.display))
        }
      />
      {favorites.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {favorites.map((code) => (
            <Button
              key={code}
              type="button"
              variant="secondary"
              disabled={disabled}
              onClick={() => onFavorite(code)}
            >
              {t("assessment.favorite", { code })}
            </Button>
          ))}
        </div>
      ) : null}
      {doctorFavorites.length > 0 ? (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t("assessment.doctorFavorites")}
          </p>
          <div className="flex flex-wrap gap-2">
            {doctorFavorites.map((favorite) => (
              <Button
                key={favorite.conceptPublicId}
                type="button"
                variant="secondary"
                disabled={disabled}
                onClick={() =>
                  onAdd(
                    clinicianDiagnosis(
                      favorite.conceptPublicId,
                      favorite.display,
                    ),
                  )
                }
                {...testIdProps(
                  diagnosisFavoriteTestId(favorite.conceptPublicId),
                )}
              >
                {favorite.display}
              </Button>
            ))}
          </div>
        </div>
      ) : null}
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("assessment.empty")}</p>
      ) : (
        <ul className="space-y-3">
          {rows.map((row) => (
            <li
              key={`${row.conceptPublicId}:${row.laterality}`}
              className="space-y-2 rounded-lg border border-border p-3"
              {...testIdProps(
                diagnosisRowTestId(row.conceptPublicId, row.laterality),
              )}
            >
              <p className="text-sm font-medium">{row.display}</p>
              {row.copied ? (
                <p className="text-xs text-muted-foreground">
                  {t("assessment.copied")}
                </p>
              ) : null}
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {t("assessment.laterality")}
              </p>
              <div className="flex flex-wrap gap-2">
                {SIDES.map((side) => (
                  <Button
                    key={side}
                    type="button"
                    size="sm"
                    variant={row.laterality === side ? "default" : "secondary"}
                    disabled={disabled}
                    aria-pressed={row.laterality === side}
                    onClick={() =>
                      onChange(row.conceptPublicId, row.laterality, {
                        laterality: side,
                      })
                    }
                  >
                    {diagnosisSideLabel(t, side)}
                  </Button>
                ))}
              </div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {t("assessment.status")}
              </p>
              <div className="flex flex-wrap gap-2">
                {STATUSES.map((status) => (
                  <Button
                    key={status}
                    type="button"
                    size="sm"
                    variant={row.status === status ? "default" : "secondary"}
                    disabled={disabled}
                    aria-pressed={row.status === status}
                    onClick={() =>
                      onChange(row.conceptPublicId, row.laterality, { status })
                    }
                  >
                    {diagnosisStatusLabel(t, status)}
                  </Button>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  disabled={row.promoted}
                  onClick={() => onPromote(row)}
                >
                  {row.promoted
                    ? t("assessment.promoted")
                    : t("assessment.promote")}
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => onSaveFavorite(row)}
                  {...testIdProps(
                    diagnosisSaveFavoriteTestId(
                      row.conceptPublicId,
                      row.laterality,
                    ),
                  )}
                >
                  {t("assessment.saveFavorite")}
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  disabled={disabled}
                  onClick={() => onRemove(row.conceptPublicId, row.laterality)}
                >
                  {t("assessment.remove")}
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
      <TextAreaField
        name="assessmentNote"
        label={t("assessment.note")}
        disabled={disabled}
      />
    </section>
  );
}
