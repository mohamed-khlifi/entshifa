"use client";

import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import type { ResolvedConcept } from "@/lib/api/generated";
import {
  laryngoscopyLesionCellTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

export type VocalFoldLesionView = {
  laterality: "right" | "left";
  thirdCode: string;
  surfaceCode: string;
  findingCode: string;
  sizeMm: number | null;
  reinkeGrade: number | null;
};

export type VocalFoldDiagramProps = {
  lesions: readonly VocalFoldLesionView[];
  thirds: readonly ResolvedConcept[];
  surfaces: readonly ResolvedConcept[];
  findings: readonly ResolvedConcept[];
  reinkeCode: string;
  reinkeGrades: readonly number[];
  readOnly: boolean;
  onAdd: (lesion: VocalFoldLesionView) => void;
  onChange: (index: number, lesion: VocalFoldLesionView) => void;
  onRemove: (index: number) => void;
};

export function VocalFoldDiagram({
  lesions,
  thirds,
  surfaces,
  findings,
  reinkeCode,
  reinkeGrades,
  readOnly,
  onAdd,
  onChange,
  onRemove,
}: VocalFoldDiagramProps) {
  const t = useTranslations("laryngoscopy");
  const firstFinding = findings[0]?.code ?? "";
  const sides = ["right", "left"] as const;

  return (
    <section className="space-y-3" {...testIdProps(testIds.laryngoscopy.folds)}>
      <h3 className="text-sm font-semibold">{t("lesions.title")}</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {sides.map((side) => (
          <div
            key={side}
            className="space-y-2 rounded-xl border border-border p-3"
          >
            <p className="text-sm font-medium">
              {side === "right" ? t("fields.rightFold") : t("fields.leftFold")}
            </p>
            {thirds.map((third) =>
              surfaces.map((surface) => (
                <Button
                  key={`${third.code}:${surface.code}`}
                  type="button"
                  variant="secondary"
                  size="sm"
                  disabled={readOnly || firstFinding.length === 0}
                  onClick={() =>
                    onAdd({
                      laterality: side,
                      thirdCode: third.code,
                      surfaceCode: surface.code,
                      findingCode: firstFinding,
                      sizeMm: null,
                      reinkeGrade: firstFinding === reinkeCode ? 1 : null,
                    })
                  }
                  {...testIdProps(
                    laryngoscopyLesionCellTestId(
                      side,
                      third.code,
                      surface.code,
                    ),
                  )}
                >
                  {t("lesions.add")}
                  <span className="ms-2 text-xs text-muted-foreground">
                    {third.display} · {surface.display}
                  </span>
                </Button>
              )),
            )}
          </div>
        ))}
      </div>
      {lesions.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("lesions.empty")}</p>
      ) : (
        <ul className="space-y-2">
          {lesions.map((lesion, index) => (
            <li
              key={`${lesion.laterality}:${lesion.thirdCode}:${lesion.surfaceCode}:${index}`}
              className="grid gap-2 rounded-xl border border-border p-3 sm:grid-cols-[minmax(0,1fr)_6rem_6rem_auto]"
            >
              <label className="space-y-1 text-sm">
                {t("lesions.finding")}
                <select
                  className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                  disabled={readOnly}
                  value={lesion.findingCode}
                  onChange={(event) => {
                    const findingCode = event.target.value;
                    onChange(index, {
                      ...lesion,
                      findingCode,
                      reinkeGrade: findingCode === reinkeCode ? 1 : null,
                    });
                  }}
                >
                  {findings.map((finding) => (
                    <option key={finding.code} value={finding.code}>
                      {finding.display}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-1 text-sm">
                {t("lesions.size")}
                <input
                  type="number"
                  min={0}
                  max={50}
                  className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                  disabled={readOnly}
                  value={lesion.sizeMm ?? ""}
                  onChange={(event) =>
                    onChange(index, {
                      ...lesion,
                      sizeMm:
                        event.target.value === ""
                          ? null
                          : Number.parseInt(event.target.value, 10),
                    })
                  }
                />
              </label>
              {lesion.findingCode === reinkeCode ? (
                <label className="space-y-1 text-sm">
                  {t("lesions.reinke")}
                  <select
                    className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm"
                    disabled={readOnly}
                    value={lesion.reinkeGrade ?? 1}
                    onChange={(event) =>
                      onChange(index, {
                        ...lesion,
                        reinkeGrade: Number.parseInt(event.target.value, 10),
                      })
                    }
                  >
                    {reinkeGrades.map((grade) => (
                      <option key={grade} value={grade}>
                        {grade}
                      </option>
                    ))}
                  </select>
                </label>
              ) : (
                <span />
              )}
              <Button
                type="button"
                variant="ghost"
                disabled={readOnly}
                onClick={() => onRemove(index)}
              >
                {t("lesions.remove")}
              </Button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
