"use client";

import { useMemo, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import { AnatomicalMap } from "@/components/clinical/AnatomicalMap/AnatomicalMap";
import { Button } from "@/components/ui/button";
import { CopyForwardPanel } from "./CopyForwardPanel";
import { NormalsToolbar } from "./NormalsToolbar";
import {
  useCopyEncounterForward,
  useCreateExaminationEncounter,
  useEncounterObservations,
  useExaminationProblems,
  useExaminationSites,
  useExaminationValueSets,
  useNarrativePreview,
  usePatientEncounters,
  useRecordObservations,
  useRecordSnapshot,
} from "../hooks/use-examination";
import { selectCopySource } from "../lib/copy-source";
import {
  anatomicalMaps,
  nasalCavityMap,
  neckLevelsMap,
  oralCavityMap,
  tympanicMembraneMap,
} from "@/lib/anatomy";
import {
  confirmAllMarks,
  confirmMark,
  effectiveLaterality,
  examinationStateFromCopy,
  hasDirtyExamination,
  markAllNormal,
  markFromFinding,
  markNormal,
  markNotExamined,
  markSectionNormal,
  regionStorageKey,
  toAllObservationCreates,
  toFullNarrativeDrafts,
} from "@/lib/anatomy/examination-state";
import { examinationMapTitle } from "@/lib/anatomy/region-labels";
import type {
  MapFindingOption,
  MapRegionDefinition,
  MapState,
  RegionMark,
} from "@/lib/anatomy/types";
import type {
  CodeableConcept,
  EncounterRead,
  ExaminationSnapshotCreate,
} from "@/lib/api/generated";
import { formatDate } from "@/lib/i18n/format";
import { examinationMapTestId, testIdProps, testIds } from "@/lib/test/test-id";

const initialMapState: MapState = { side: "right", marks: {} };

type CopySession = {
  sourceEncounterId: string;
  sourceStartedAt: string;
  historyText: string | null;
  chiefComplaintSummary: string | null;
  complaints: { id: string; label: string }[];
  assessmentText: string | null;
  planText: string | null;
  confirmed: boolean;
};

export function ExaminationWorkspace({ patientId }: { patientId: string }) {
  const t = useTranslations("examination");
  const locale = useLocale();
  const encounters = usePatientEncounters(patientId);
  const [mapId, setMapId] = useState(anatomicalMaps[0].id);
  const [byMap, setByMap] = useState<Record<string, MapState>>({});
  const [encounterId, setEncounterId] = useState<string | null>(null);
  const [createdEncounter, setCreatedEncounter] =
    useState<EncounterRead | null>(null);
  const [copySession, setCopySession] = useState<CopySession | null>(null);
  const definition =
    anatomicalMaps.find((map) => map.id === mapId) ?? anatomicalMaps[0];
  const mapState = byMap[definition.id] ?? initialMapState;
  const rows = useMemo(() => {
    const items = encounters.data?.items ?? [];
    if (
      !createdEncounter ||
      items.some((row) => row.publicId === createdEncounter.publicId)
    ) {
      return items;
    }
    return [createdEncounter, ...items];
  }, [encounters.data?.items, createdEncounter]);
  const selectedEncounter =
    rows.find((row) => row.publicId === encounterId) ??
    rows.find((row) => row.status === "draft") ??
    rows[0] ??
    null;
  const activeEncounterId = selectedEncounter?.publicId ?? null;
  const copySource = selectCopySource(rows, activeEncounterId);

  const valueSetCodes = useMemo(
    () => [...new Set(definition.regions.map((region) => region.valueSetCode))],
    [definition],
  );
  const valueSetQueries = useExaminationValueSets(valueSetCodes);
  const drafts = toFullNarrativeDrafts(anatomicalMaps, byMap);
  const narrative = useNarrativePreview(
    patientId,
    "full",
    drafts.length > 0 ? { findings: drafts } : null,
  );
  const save = useRecordObservations(patientId);
  const snapshot = useRecordSnapshot(patientId);
  const sites = useExaminationSites();
  const createEncounter = useCreateExaminationEncounter(patientId);
  const copyForward = useCopyEncounterForward(patientId);
  const copiedObservations = useEncounterObservations(
    copySession?.sourceEncounterId ?? null,
  );
  const problems = useExaminationProblems(patientId, copySession !== null);
  const hasFindings = hasDirtyExamination(anatomicalMaps, byMap);
  const writing =
    save.isPending ||
    snapshot.isPending ||
    createEncounter.isPending ||
    copyForward.isPending;
  const canAttach =
    selectedEncounter?.status === "draft" ||
    rows.some((row) => row.status === "draft") ||
    (sites.data?.items.length ?? 0) > 0;
  const findingCount =
    copiedObservations.data?.page.total ??
    copiedObservations.data?.items.length ??
    0;
  const problemLines = (problems.data?.items ?? []).flatMap((row) => {
    if (row.status !== "active") {
      return [];
    }
    const label = codedLabel(row.diagnosis);
    return label ? [{ id: row.publicId, label }] : [];
  });

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

  function applySection(
    target: (typeof anatomicalMaps)[number],
    side?: MapState["side"],
  ) {
    setMapId(target.id);
    setByMap((current) => {
      const existing = current[target.id] ?? initialMapState;
      return {
        ...current,
        [target.id]: {
          side: side ?? existing.side,
          marks: {
            ...existing.marks,
            ...markSectionNormal(target, side),
          },
        },
      };
    });
  }

  async function encounterForWrite(): Promise<string | null> {
    if (selectedEncounter?.status === "draft") {
      return selectedEncounter.publicId;
    }
    const draft = rows.find((row) => row.status === "draft");
    if (draft) {
      setEncounterId(draft.publicId);
      return draft.publicId;
    }
    const site =
      sites.data?.items.find((item) => item.isPrimary) ?? sites.data?.items[0];
    if (!site) {
      toast.error(t("actions.needsSite"));
      return null;
    }
    const created = await createEncounter.mutateAsync({
      patientPublicId: patientId,
      sitePublicId: site.publicId,
      encounterType: "consultation",
      startedAt: new Date().toISOString(),
    });
    setCreatedEncounter(created);
    setEncounterId(created.publicId);
    return created.publicId;
  }

  async function handleSave() {
    if (!hasFindings) {
      return;
    }
    try {
      const encounterPublicId = await encounterForWrite();
      if (!encounterPublicId) {
        return;
      }
      save.mutate(
        {
          encounterPublicId,
          observations: toAllObservationCreates(
            anatomicalMaps,
            byMap,
            new Date().toISOString(),
          ),
        },
        {
          onSuccess: () => {
            toast.success(t("actions.saved"));
          },
        },
      );
    } catch {
      return;
    }
  }

  async function handleSnapshot() {
    let encounterPublicId: string | null = null;
    if (canAttach) {
      try {
        encounterPublicId = await encounterForWrite();
      } catch {
        return;
      }
    }
    snapshot.mutate(
      {
        encounterPublicId,
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
  }

  async function handleCopy() {
    if (!copySource) {
      return;
    }
    try {
      const result = await copyForward.mutateAsync({
        sourceEncounterId: copySource.publicId,
        body: {
          sitePublicId: copySource.sitePublicId,
          startedAt: new Date().toISOString(),
        },
      });
      setCreatedEncounter(result.encounter);
      setEncounterId(result.encounter.publicId);
      setCopySession(sessionFromCopy(copySource, result.encounter));
      setByMap(
        examinationStateFromCopy(
          anatomicalMaps,
          result.observations.items,
          result.snapshots.items,
          copySource.publicId,
        ),
      );
    } catch {
      return;
    }
  }

  function handleConfirmAll() {
    setByMap((current) => {
      const next: Record<string, MapState> = {};
      for (const [id, state] of Object.entries(current)) {
        next[id] = { ...state, marks: confirmAllMarks(state.marks) };
      }
      return next;
    });
    setCopySession((current) =>
      current ? { ...current, confirmed: true } : current,
    );
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

  function confirmRegion(region: MapRegionDefinition) {
    const laterality = effectiveLaterality(region, mapState.side);
    const key = regionStorageKey(laterality, region.id);
    const mark = mapState.marks[key];
    if (!mark) {
      return;
    }
    putMark(region, confirmMark(mark));
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
      <NormalsToolbar
        canCopy={copySource !== null}
        copying={copyForward.isPending}
        onNormalAll={() => setByMap(markAllNormal(anatomicalMaps))}
        onOtoscopyRight={() => applySection(tympanicMembraneMap, "right")}
        onOtoscopyLeft={() => applySection(tympanicMembraneMap, "left")}
        onRhinoscopy={() => applySection(nasalCavityMap)}
        onOral={() => applySection(oralCavityMap)}
        onNeck={() => applySection(neckLevelsMap)}
        onCopy={() => {
          void handleCopy();
        }}
        labels={{
          group: t("normals.group"),
          all: t("normals.all"),
          otoscopyRight: t("normals.otoscopyRight"),
          otoscopyLeft: t("normals.otoscopyLeft"),
          rhinoscopy: t("normals.rhinoscopy"),
          oral: t("normals.oral"),
          neck: t("normals.neck"),
          copy: t("copyForward.action"),
          unavailable: t("copyForward.unavailable"),
        }}
      />
      {copySession ? (
        <CopyForwardPanel
          whenLabel={formatDate(copySession.sourceStartedAt, locale)}
          findingCountLabel={t("copyForward.findingCount", {
            count: findingCount,
          })}
          historyText={copySession.historyText}
          chiefComplaintSummary={copySession.chiefComplaintSummary}
          complaints={copySession.complaints}
          assessmentText={copySession.assessmentText}
          planText={copySession.planText}
          problems={problemLines}
          problemsLoading={problems.isLoading}
          problemsError={problems.isError}
          confirmed={copySession.confirmed}
          onConfirmAll={handleConfirmAll}
        />
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
            {...testIdProps(examinationMapTestId(map.id))}
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
            putMark(region, markFromFinding(region, conceptCode))
          }
          onMarkNotExamined={(region) => putMark(region, markNotExamined())}
          onConfirmMark={confirmRegion}
        />
        <section className="space-y-3 rounded-xl border border-border bg-card p-4">
          <h2 className="text-sm font-medium">{t("narrative.title")}</h2>
          <NarrativePreview
            text={narrative.data?.text ?? ""}
            empty={t("narrative.empty")}
          />
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              disabled={!hasFindings || writing || !canAttach}
              onClick={() => {
                void handleSave();
              }}
              {...testIdProps(testIds.examination.save)}
            >
              {t("actions.save")}
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={writing}
              onClick={() => {
                void handleSnapshot();
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

function NarrativePreview({ text, empty }: { text: string; empty: string }) {
  const blocks = text
    .split("\n\n")
    .map((block) => block.split("\n").filter((line) => line.length > 0))
    .filter((lines) => lines.length > 0);
  if (blocks.length === 0) {
    return (
      <p
        className="min-h-16 text-sm leading-6 text-muted-foreground"
        {...testIdProps(testIds.examination.narrative)}
      >
        {empty}
      </p>
    );
  }
  return (
    <div
      className="min-h-16 space-y-4"
      {...testIdProps(testIds.examination.narrative)}
    >
      {blocks.map((lines, blockIndex) => (
        <div key={`${lines[0]}-${blockIndex}`} className="space-y-1">
          <p className="text-sm font-medium">{lines[0]}</p>
          <ul className="list-disc space-y-1 ps-5">
            {lines.slice(1).map((line, lineIndex) => (
              <li key={`${line}-${lineIndex}`} className="text-sm leading-6">
                {line}
              </li>
            ))}
          </ul>
        </div>
      ))}
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

function sessionFromCopy(
  source: EncounterRead,
  created: EncounterRead,
): CopySession {
  return {
    sourceEncounterId: source.publicId,
    sourceStartedAt: source.startedAt,
    historyText: created.historyText ?? null,
    chiefComplaintSummary: created.chiefComplaintSummary ?? null,
    complaints: created.complaints.flatMap((row) => {
      const label = codedLabel(row.concept);
      return label ? [{ id: row.publicId, label }] : [];
    }),
    assessmentText: created.assessmentText ?? null,
    planText: created.planText ?? null,
    confirmed: false,
  };
}

function codedLabel(concept: CodeableConcept): string {
  const display = concept.display?.trim();
  if (display) {
    return display;
  }
  return concept.code?.trim() ?? "";
}
