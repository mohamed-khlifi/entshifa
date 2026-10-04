"use client";

import { useMemo, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import { AnatomicalMap } from "@/components/clinical/AnatomicalMap/AnatomicalMap";
import { Button } from "@/components/ui/button";
import {
  useExaminationValueSets,
  useNarrativePreview,
  usePatientEncounters,
  useRecordObservations,
  useRecordSnapshot,
} from "../hooks/use-examination";
import { anatomicalMaps } from "@/lib/anatomy";
import {
  markFinding,
  markNormal,
  markNotExamined,
  regionStorageKey,
  effectiveLaterality,
  toNarrativeDrafts,
  toObservationCreates,
} from "@/lib/anatomy/examination-state";
import { examinationMapTitle } from "@/lib/anatomy/region-labels";
import type {
  MapFindingOption,
  MapRegionDefinition,
  MapSide,
  RegionMark,
} from "@/lib/anatomy/types";
import type { ExaminationSnapshotCreate } from "@/lib/api/generated";
import { formatDate } from "@/lib/i18n/format";
import { testIdProps, testIds } from "@/lib/test/test-id";

type MapState = {
  side: MapSide;
  marks: Record<string, RegionMark>;
};

const initialMapState: MapState = { side: "right", marks: {} };

export function ExaminationWorkspace({ patientId }: { patientId: string }) {
  const t = useTranslations("examination");
  const locale = useLocale();
  const encounters = usePatientEncounters(patientId);
  const [mapId, setMapId] = useState(anatomicalMaps[0].id);
  const [byMap, setByMap] = useState<Record<string, MapState>>({});
  const [encounterId, setEncounterId] = useState<string | null>(null);
  const definition =
    anatomicalMaps.find((map) => map.id === mapId) ?? anatomicalMaps[0];
  const mapState = byMap[definition.id] ?? initialMapState;
  const rows = encounters.data?.items ?? [];
  const selectedEncounter =
    rows.find((row) => row.publicId === encounterId) ??
    rows.find((row) => row.status === "draft") ??
    rows[0] ??
    null;
  const activeEncounterId = selectedEncounter?.publicId ?? null;

  const valueSetCodes = useMemo(
    () => [...new Set(definition.regions.map((region) => region.valueSetCode))],
    [definition],
  );
  const valueSetQueries = useExaminationValueSets(valueSetCodes);
  const drafts = toNarrativeDrafts(definition, mapState.side, mapState.marks);
  const narrative = useNarrativePreview(
    patientId,
    definition.id,
    drafts.length > 0 ? { findings: drafts } : null,
  );
  const save = useRecordObservations(patientId);
  const snapshot = useRecordSnapshot(patientId);

  const findingsByValueSet = useMemo(() => {
    const grouped: Record<string, MapFindingOption[]> = {};
    valueSetCodes.forEach((code, index) => {
      grouped[code] = (valueSetQueries[index]?.data?.members ?? []).map(
        (member) => ({
          code: member.code,
          display: member.display,
        }),
      );
    });
    return grouped;
  }, [valueSetCodes, valueSetQueries]);
  const findingsLoading = valueSetQueries.some((query) => query.isLoading);

  function updateMap(next: MapState) {
    setByMap((current) => ({ ...current, [definition.id]: next }));
  }

  function putMark(region: MapRegionDefinition, mark: RegionMark) {
    const laterality = effectiveLaterality(region, mapState.side);
    updateMap({
      side: mapState.side,
      marks: {
        ...mapState.marks,
        [regionStorageKey(laterality, region.id)]: mark,
      },
    });
  }

  return (
    <div className="space-y-6" {...testIdProps(testIds.examination.root)}>
      <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
      {encounters.isLoading ? (
        <p className="text-sm text-muted-foreground">{t("loading")}</p>
      ) : null}
      {!encounters.isLoading && rows.length === 0 ? (
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.examination.encounterEmpty)}
        >
          {t("encounter.empty")}
        </p>
      ) : null}
      {rows.length > 0 ? (
        <label className="block space-y-1 text-sm">
          <span>{t("encounter.label")}</span>
          <select
            className="h-10 w-full max-w-md rounded-lg border border-border bg-card px-3"
            value={activeEncounterId ?? ""}
            onChange={(event) => setEncounterId(event.target.value)}
            {...testIdProps(testIds.examination.encounter)}
          >
            {rows.map((row) => (
              <option key={row.publicId} value={row.publicId}>
                {t("encounter.option", {
                  when: formatDate(row.startedAt, locale),
                  status: encounterStatusLabel(t, row.status),
                })}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      <div
        className="flex flex-wrap gap-2"
        {...testIdProps(testIds.examination.mapSelect)}
      >
        {anatomicalMaps.map((map) => (
          <Button
            key={map.id}
            type="button"
            variant={map.id === definition.id ? "default" : "secondary"}
            onClick={() => setMapId(map.id)}
          >
            {examinationMapTitle(t, map.titleKey)}
          </Button>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,28rem)_minmax(0,1fr)]">
        <AnatomicalMap
          key={definition.id}
          definition={definition}
          selectedSide={mapState.side}
          marks={mapState.marks}
          findingsByValueSet={findingsByValueSet}
          findingsLoading={findingsLoading}
          onSelectedSideChange={(side) => updateMap({ ...mapState, side })}
          onMarkNormal={(region) => putMark(region, markNormal(region))}
          onSelectFinding={(region, conceptCode) =>
            putMark(region, markFinding(conceptCode))
          }
          onMarkNotExamined={(region) => putMark(region, markNotExamined())}
        />
        <section className="space-y-3 rounded-xl border border-border bg-card p-4">
          <h2 className="text-sm font-medium">{t("narrative.title")}</h2>
          <p
            className="min-h-16 text-sm leading-6"
            dir="ltr"
            {...testIdProps(testIds.examination.narrative)}
          >
            {narrative.data?.text || t("narrative.empty")}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              disabled={!activeEncounterId || save.isPending}
              onClick={() => {
                if (!activeEncounterId) {
                  return;
                }
                const observations = toObservationCreates(
                  definition,
                  mapState.side,
                  mapState.marks,
                  new Date().toISOString(),
                );
                if (observations.length === 0) {
                  return;
                }
                save.mutate(
                  {
                    encounterPublicId: activeEncounterId,
                    observations,
                  },
                  {
                    onSuccess: () => {
                      toast.success(t("actions.saved"));
                    },
                  },
                );
              }}
              {...testIdProps(testIds.examination.save)}
            >
              {t("actions.save")}
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={!activeEncounterId || snapshot.isPending}
              onClick={() => {
                if (!activeEncounterId) {
                  return;
                }
                snapshot.mutate(
                  {
                    encounterPublicId: activeEncounterId,
                    mapId: definition.id,
                    laterality: mapState.side,
                    payload: {
                      side: mapState.side,
                      marks: mapState.marks,
                    } as unknown as ExaminationSnapshotCreate["payload"],
                  },
                  {
                    onSuccess: () => {
                      toast.success(t("actions.snapshotSaved"));
                    },
                  },
                );
              }}
              {...testIdProps(testIds.examination.snapshot)}
            >
              {t("actions.saveSnapshot")}
            </Button>
          </div>
        </section>
      </div>
    </div>
  );
}

function encounterStatusLabel(
  t: ReturnType<typeof useTranslations<"examination">>,
  status: string,
): string {
  switch (status) {
    case "draft":
      return t("encounter.status.draft");
    case "signed":
      return t("encounter.status.signed");
    case "amended":
      return t("encounter.status.amended");
    default:
      return t("encounter.status.other");
  }
}
