"use client";

import { useTranslations } from "next-intl";
import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { examinationRegionLabel } from "@/lib/anatomy/region-labels";
import {
  effectiveLaterality,
  regionStorageKey,
} from "@/lib/anatomy/examination-state";
import type {
  AnatomicalMapDefinition,
  MapFindingOption,
  MapRegionDefinition,
  MapSide,
  RegionMark,
} from "@/lib/anatomy/types";
import {
  examinationFindingTestId,
  examinationRegionTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

export type AnatomicalMapProps = {
  definition: AnatomicalMapDefinition;
  selectedSide: MapSide;
  marks: Readonly<Record<string, RegionMark>>;
  findingsByValueSet: Readonly<Record<string, readonly MapFindingOption[]>>;
  findingsLoading?: boolean;
  svgMarkup?: string;
  onSelectedSideChange: (side: MapSide) => void;
  onMarkNormal: (region: MapRegionDefinition) => void;
  onSelectFinding: (region: MapRegionDefinition, conceptCode: string) => void;
  onMarkNotExamined: (region: MapRegionDefinition) => void;
  onAttachPhoto?: (region: MapRegionDefinition) => void;
};

export function AnatomicalMap({
  definition,
  selectedSide,
  marks,
  findingsByValueSet,
  findingsLoading = false,
  svgMarkup,
  onSelectedSideChange,
  onSelectFinding,
  onMarkNormal,
  onMarkNotExamined,
  onAttachPhoto,
}: AnatomicalMapProps) {
  const t = useTranslations("examination");
  const hostRef = useRef<HTMLDivElement>(null);
  const handlersRef = useRef<{
    activateRegion: (region: MapRegionDefinition) => void;
    handleRegionKey: (event: KeyboardEvent, index: number) => void;
    onAttachPhoto?: AnatomicalMapProps["onAttachPhoto"];
  } | null>(null);
  const [fetched, setFetched] = useState("");
  const [focusIndex, setFocusIndex] = useState(0);
  const [pickerRegionId, setPickerRegionId] = useState<string | null>(null);
  const focusIntentRef = useRef<"mount" | "keyboard" | "none">("mount");
  const labelId = useId();
  const markup = svgMarkup ?? fetched;

  useEffect(() => {
    if (svgMarkup) {
      return;
    }
    let cancelled = false;
    void fetch(definition.svg)
      .then((response) => response.text())
      .then((text) => {
        if (!cancelled) {
          setFetched(text);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFetched("");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [definition.svg, svgMarkup]);

  useLayoutEffect(() => {
    const host = hostRef.current;
    if (!host) {
      return;
    }
    while (host.firstChild) {
      host.removeChild(host.firstChild);
    }
    if (!markup) {
      return;
    }
    const parsed = new DOMParser().parseFromString(markup, "image/svg+xml");
    const parsedSvg = parsed.documentElement;
    if (parsedSvg.namespaceURI !== "http://www.w3.org/2000/svg") {
      return;
    }
    const svg = host.ownerDocument.importNode(parsedSvg, true);
    host.append(svg);
    const cleanups: Array<() => void> = [];
    definition.regions.forEach((region, index) => {
      const node = host.querySelector(`#${region.pathId}`);
      if (!(node instanceof SVGElement)) {
        return;
      }
      node.setAttribute("role", "button");
      node.setAttribute("data-region-id", region.id);
      node.setAttribute("data-testid", examinationRegionTestId(region.id));
      const onClick = () => {
        handlersRef.current?.activateRegion(region);
      };
      const onKeyDown = (event: Event) => {
        if (!(event instanceof KeyboardEvent)) {
          return;
        }
        handlersRef.current?.handleRegionKey(event, index);
      };
      const onContextMenu = (event: Event) => {
        event.preventDefault();
        handlersRef.current?.onAttachPhoto?.(region);
      };
      node.addEventListener("click", onClick);
      node.addEventListener("keydown", onKeyDown);
      node.addEventListener("contextmenu", onContextMenu);
      cleanups.push(() => {
        node.removeEventListener("click", onClick);
        node.removeEventListener("keydown", onKeyDown);
        node.removeEventListener("contextmenu", onContextMenu);
      });
    });
    return () => {
      for (const cleanup of cleanups) {
        cleanup();
      }
      while (host.firstChild) {
        host.removeChild(host.firstChild);
      }
    };
  }, [markup, definition]);

  useLayoutEffect(() => {
    const host = hostRef.current;
    if (!host) {
      return;
    }
    definition.regions.forEach((region, index) => {
      const node = host.querySelector(`#${region.pathId}`);
      if (!(node instanceof SVGElement)) {
        return;
      }
      const laterality = effectiveLaterality(region, selectedSide);
      const mark = marks[regionStorageKey(laterality, region.id)];
      node.setAttribute("data-state", mark?.status ?? "not_examined");
      node.setAttribute("tabindex", index === focusIndex ? "0" : "-1");
      node.setAttribute(
        "aria-label",
        examinationRegionLabel(t, region.labelKey),
      );
    });
    if (focusIntentRef.current === "none") {
      return;
    }
    const current = definition.regions[focusIndex];
    const focused = current ? host.querySelector(`#${current.pathId}`) : null;
    if (focused instanceof SVGElement) {
      focused.focus({ preventScroll: true });
      focusIntentRef.current = "none";
    }
  }, [markup, definition, marks, selectedSide, focusIndex, t]);

  function activateRegion(region: MapRegionDefinition) {
    const laterality = effectiveLaterality(region, selectedSide);
    const mark = marks[regionStorageKey(laterality, region.id)];
    if (!mark || mark.status === "not_examined") {
      onMarkNormal(region);
      setPickerRegionId(null);
      return;
    }
    setPickerRegionId(region.id);
  }

  function handleRegionKey(event: KeyboardEvent, index: number) {
    if (event.key === "ArrowDown" || event.key === "ArrowRight") {
      event.preventDefault();
      focusIntentRef.current = "keyboard";
      setFocusIndex((index + 1) % definition.regions.length);
      return;
    }
    if (event.key === "ArrowUp" || event.key === "ArrowLeft") {
      event.preventDefault();
      focusIntentRef.current = "keyboard";
      setFocusIndex(
        (index - 1 + definition.regions.length) % definition.regions.length,
      );
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      const region = definition.regions[index];
      if (region) {
        activateRegion(region);
      }
      return;
    }
    if (!definition.paired) {
      return;
    }
    if (event.key === "r" || event.key === "R") {
      event.preventDefault();
      onSelectedSideChange("right");
    }
    if (event.key === "l" || event.key === "L") {
      event.preventDefault();
      onSelectedSideChange("left");
    }
  }

  handlersRef.current = {
    activateRegion,
    handleRegionKey,
    onAttachPhoto,
  };

  const pickerRegion =
    definition.regions.find((region) => region.id === pickerRegionId) ?? null;
  const findings = pickerRegion
    ? (findingsByValueSet[pickerRegion.valueSetCode] ?? [])
    : [];

  return (
    <div className="space-y-3" {...testIdProps(testIds.examination.map.root)}>
      {definition.paired ? (
        <div className="flex gap-2" role="group" aria-labelledby={labelId}>
          <span id={labelId} className="sr-only">
            {t("laterality.group")}
          </span>
          <Button
            type="button"
            variant={selectedSide === "right" ? "default" : "secondary"}
            onClick={() => onSelectedSideChange("right")}
            {...testIdProps(testIds.examination.map.lateralityRight)}
          >
            {t("laterality.right")}
          </Button>
          <Button
            type="button"
            variant={selectedSide === "left" ? "default" : "secondary"}
            onClick={() => onSelectedSideChange("left")}
            {...testIdProps(testIds.examination.map.lateralityLeft)}
          >
            {t("laterality.left")}
          </Button>
        </div>
      ) : null}
      <div
        ref={hostRef}
        dir="ltr"
        className={cn(
          "anatomical-map max-w-md rounded-xl border border-border bg-card p-3",
          "[&_svg]:h-auto [&_svg]:w-full",
          "[&_[data-region-id]]:cursor-pointer [&_[data-region-id]]:stroke-current",
          "[&_[data-region-id]]:fill-transparent [&_[data-region-id]]:stroke-[1.5]",
          "[&_[data-state=normal]]:fill-emerald-500/35",
          "[&_[data-state=abnormal]]:fill-amber-500/50",
          "[&_[data-region-id]:focus]:outline [&_[data-region-id]:focus]:outline-2",
          "[&_[data-region-id]:focus]:outline-offset-2 [&_[data-region-id]:focus]:outline-ring",
        )}
      />
      {pickerRegion ? (
        <div
          className="space-y-2 rounded-xl border border-border bg-card p-3"
          aria-label={t("findingPicker.title")}
          {...testIdProps(testIds.examination.map.findingPicker)}
        >
          <p className="text-sm font-medium">
            {examinationRegionLabel(t, pickerRegion.labelKey)}
          </p>
          {findingsLoading ? (
            <p className="text-sm text-muted-foreground">
              {t("findingPicker.loading")}
            </p>
          ) : null}
          {!findingsLoading && findings.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {t("findingPicker.empty")}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-2">
            {findings.map((finding) => (
              <Button
                key={finding.code}
                type="button"
                variant="secondary"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => {
                  onSelectFinding(pickerRegion, finding.code);
                  setPickerRegionId(null);
                }}
                {...testIdProps(examinationFindingTestId(finding.code))}
              >
                {finding.display}
              </Button>
            ))}
          </div>
          <Button
            type="button"
            variant="ghost"
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => {
              onMarkNotExamined(pickerRegion);
              setPickerRegionId(null);
            }}
            {...testIdProps(testIds.examination.map.notExamined)}
          >
            {t("actions.notExamined")}
          </Button>
        </div>
      ) : null}
    </div>
  );
}

export function svgMarkupForMap(definition: AnatomicalMapDefinition): string {
  const shapes = definition.regions
    .map((region) => `<path id="${region.pathId}" d="M0 0h12v12h-12z"></path>`)
    .join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">${shapes}</svg>`;
}
