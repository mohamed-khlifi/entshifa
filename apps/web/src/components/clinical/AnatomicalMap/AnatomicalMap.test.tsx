import { cleanup, fireEvent, render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactElement } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  AnatomicalMap,
  svgMarkupForMap,
  type AnatomicalMapProps,
} from "@/components/clinical/AnatomicalMap/AnatomicalMap";
import { markNormal, regionStorageKey } from "@/lib/anatomy/examination-state";
import { anatomicalMaps } from "@/lib/anatomy";
import { tympanicMembraneMap } from "@/lib/anatomy/tympanic-membrane.map";
import {
  examinationMapTitle,
  examinationRegionLabel,
} from "@/lib/anatomy/region-labels";
import {
  examinationFindingTestId,
  examinationRegionTestId,
  testIds,
} from "@/lib/test/test-id";

const messages = {
  examination: {
    laterality: { group: "Side", right: "Right", left: "Left" },
    findingPicker: {
      title: "Finding",
      loading: "Loading findings…",
      empty: "No findings are configured for this region.",
    },
    actions: { notExamined: "Not examined" },
    regions: { unknown: "Region" },
    maps: {
      tympanicMembrane: "Tympanic membrane",
      nasalCavity: "Nasal cavity",
      oralCavity: "Oral cavity and oropharynx",
      neckLevels: "Neck",
    },
    tm: {
      regions: {
        canal: "External auditory canal",
        parsFlaccida: "Pars flaccida",
        anteroSuperior: "Anterosuperior quadrant",
        anteroInferior: "Anteroinferior quadrant",
        posteroSuperior: "Posterosuperior quadrant",
        posteroInferior: "Posteroinferior quadrant",
      },
    },
    nose: { regions: {} },
    oral: { regions: {} },
    neck: { regions: {} },
  },
};

afterEach(() => {
  cleanup();
});

function renderMap(overrides: Partial<AnatomicalMapProps> = {}) {
  const props: AnatomicalMapProps = {
    definition: tympanicMembraneMap,
    selectedSide: "right",
    marks: {},
    findingsByValueSet: {
      "tm.canal.findings": [{ code: "FIND.CANAL.WAX", display: "Wax" }],
      "tm.findings": [{ code: "FIND.TM.PERFORATION", display: "Perforation" }],
    },
    svgMarkup: svgMarkupForMap(tympanicMembraneMap),
    onSelectedSideChange: () => undefined,
    onMarkNormal: () => undefined,
    onSelectFinding: () => undefined,
    onMarkNotExamined: () => undefined,
    ...overrides,
  };
  const view = render(wrap(props));
  return { ...view, props };
}

function wrap(props: AnatomicalMapProps): ReactElement {
  return (
    <div dir="rtl">
      <NextIntlClientProvider locale="en" messages={messages}>
        <AnatomicalMap {...props} />
      </NextIntlClientProvider>
    </div>
  );
}

describe("AnatomicalMap", () => {
  it("keeps the diagram left-to-right inside an RTL page", () => {
    const view = renderMap();
    const diagram = view.container.querySelector(".anatomical-map");
    expect(diagram?.getAttribute("dir")).toBe("ltr");
  });

  it("moves focus through every region in anatomical order", () => {
    const view = renderMap();
    const ids = tympanicMembraneMap.regions.map((region) =>
      examinationRegionTestId(region.id),
    );
    let current = view.getByTestId(ids[0] ?? "");
    expect(document.activeElement).toBe(current);
    for (let index = 1; index < ids.length; index += 1) {
      fireEvent.keyDown(current, { key: "ArrowDown" });
      current = view.getByTestId(ids[index] ?? "");
      expect(document.activeElement).toBe(current);
    }
  });

  it("marks a region normal, then records the chosen finding", () => {
    const onMarkNormal = vi.fn();
    const onSelectFinding = vi.fn();
    const view = renderMap({ onMarkNormal, onSelectFinding });
    const canal = view.getByTestId(examinationRegionTestId("tm.canal"));
    fireEvent.click(canal);
    expect(onMarkNormal).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "tm.canal",
        bodySiteCode: "ANAT.EAR.CANAL",
        defaultNormalCode: "FIND.CANAL.NORMAL",
      }),
    );

    const marked = {
      [regionStorageKey("right", "tm.canal")]: markNormal(
        tympanicMembraneMap.regions[0]!,
      ),
    };
    view.rerender(
      wrap({
        ...view.props,
        onMarkNormal,
        onSelectFinding,
        marks: marked,
      }),
    );
    fireEvent.click(view.getByTestId(examinationRegionTestId("tm.canal")));
    expect(
      view.getByTestId(testIds.examination.map.findingPicker),
    ).toBeTruthy();
    fireEvent.click(
      view.getByTestId(examinationFindingTestId("FIND.CANAL.WAX")),
    );
    expect(onSelectFinding).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "tm.canal",
        bodySiteCode: "ANAT.EAR.CANAL",
      }),
      "FIND.CANAL.WAX",
    );
  });
});

describe("examination labels", () => {
  it("resolves every map region and title through the catalog", () => {
    const t = ((key: string) => key) as ReturnType<
      typeof import("next-intl").useTranslations<"examination">
    >;
    for (const map of anatomicalMaps) {
      expect(examinationMapTitle(t, map.titleKey)).toBe(map.titleKey);
      for (const region of map.regions) {
        expect(examinationRegionLabel(t, region.labelKey)).toBe(
          region.labelKey,
        );
      }
    }
  });
});
