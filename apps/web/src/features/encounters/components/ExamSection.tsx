"use client";

import { useMemo } from "react";
import { useQueries } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";

import { AnatomicalMap } from "@/components/clinical/AnatomicalMap/AnatomicalMap";
import { Button } from "@/components/ui/button";
import { anatomicalMaps } from "@/lib/anatomy";
import {
  effectiveLaterality,
  markFromFinding,
  markNormal,
  markNotExamined,
  regionStorageKey,
} from "@/lib/anatomy/examination-state";
import { examinationMapTitle } from "@/lib/anatomy/region-labels";
import type {
  MapFindingOption,
  MapRegionDefinition,
  MapState,
} from "@/lib/anatomy/types";
import { queryKeys } from "@/lib/api/query-keys";
import {
  encounterMapToggleTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

import { fetchExamValueSet } from "../api/encounters.api";

const initialMapState: MapState = { side: "right", marks: {} };

type ExamSectionProps = {
  byMap: Record<string, MapState>;
  expanded: readonly string[];
  disabled: boolean;
  onChange: (next: Record<string, MapState>) => void;
  onToggle: (mapId: string) => void;
};

export function ExamSection({
  byMap,
  expanded,
  disabled,
  onChange,
  onToggle,
}: ExamSectionProps) {
  const tExam = useTranslations("examination");
  const t = useTranslations("encounters");
  const locale = useLocale();
  const { session } = useSession();
  const scope = {
    locale,
    clinicPublicId: session?.clinicPublicId ?? "",
    enabled: Boolean(session?.clinicPublicId),
  };
  const valueSetCodes = useMemo(
    () => [
      ...new Set(
        anatomicalMaps.flatMap((map) =>
          map.regions.map((region) => region.valueSetCode),
        ),
      ),
    ],
    [],
  );
  const valueSets = useQueries({
    queries: valueSetCodes.map((code) => ({
      queryKey: queryKeys.examination.valueSet(code, locale),
      queryFn: () => fetchExamValueSet(code, scope),
      enabled: scope.enabled,
      staleTime: 3_600_000,
    })),
  });
  const findingsByValueSet = useMemo(() => {
    const grouped: Record<string, MapFindingOption[]> = {};
    valueSetCodes.forEach((code, index) => {
      grouped[code] = (valueSets[index]?.data?.members ?? []).map((member) => ({
        code: member.code,
        display: member.display,
      }));
    });
    return grouped;
  }, [valueSetCodes, valueSets]);

  function updateMap(mapId: string, recipe: (state: MapState) => MapState) {
    const current = byMap[mapId] ?? initialMapState;
    onChange({ ...byMap, [mapId]: recipe(current) });
  }

  return (
    <section className="space-y-3" {...testIdProps(testIds.encounters.exam)}>
      <h2 className="text-lg font-semibold">{t("exam.title")}</h2>
      {anatomicalMaps.map((definition) => {
        const open = expanded.includes(definition.id);
        const state = byMap[definition.id] ?? initialMapState;
        return (
          <div key={definition.id} className="space-y-2">
            <Button
              type="button"
              variant="secondary"
              aria-expanded={open}
              disabled={disabled}
              onClick={() => onToggle(definition.id)}
              {...testIdProps(encounterMapToggleTestId(definition.id))}
            >
              <span>{examinationMapTitle(tExam, definition.titleKey)}</span>
              <span>{open ? t("exam.collapse") : t("exam.expand")}</span>
            </Button>
            {open ? (
              <AnatomicalMap
                definition={definition}
                selectedSide={state.side}
                marks={state.marks}
                findingsByValueSet={findingsByValueSet}
                findingsLoading={valueSets.some((query) => query.isLoading)}
                onSelectedSideChange={(side) =>
                  updateMap(definition.id, (current) => ({ ...current, side }))
                }
                onMarkNormal={(region) =>
                  put(
                    definition.id,
                    state,
                    region,
                    markNormal(region),
                    onChange,
                    byMap,
                  )
                }
                onSelectFinding={(region, conceptCode) =>
                  put(
                    definition.id,
                    state,
                    region,
                    markFromFinding(region, conceptCode),
                    onChange,
                    byMap,
                  )
                }
                onMarkNotExamined={(region) =>
                  put(
                    definition.id,
                    state,
                    region,
                    markNotExamined(),
                    onChange,
                    byMap,
                  )
                }
              />
            ) : null}
          </div>
        );
      })}
    </section>
  );
}

function put(
  mapId: string,
  state: MapState,
  region: MapRegionDefinition,
  mark: ReturnType<typeof markNormal>,
  onChange: (next: Record<string, MapState>) => void,
  byMap: Record<string, MapState>,
) {
  const laterality = effectiveLaterality(region, state.side);
  onChange({
    ...byMap,
    [mapId]: {
      ...state,
      marks: {
        ...state.marks,
        [regionStorageKey(laterality, region.id)]: mark,
      },
    },
  });
}
