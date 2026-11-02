"use client";

import { useTranslations } from "next-intl";
import { useCallback, useMemo } from "react";

import { GRID_ROWS, BONE_FREQUENCIES_HZ } from "../../constants";
import { gridRowLabel } from "../../lib/labels";
import type {
  ActivePlotMode,
  ThresholdCell,
} from "../../types/audiology.types";
import {
  cellKey,
  frequencyAllowed,
  setCellValue,
  snapLevelDb,
  toggleNoResponse,
} from "../../utils/audiogram.utils";
import {
  audiogramCellTestId,
  audiogramNoResponseTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

type AudiogramGridProps = {
  frequencies: number[];
  cells: Record<string, ThresholdCell>;
  activeMode: ActivePlotMode;
  focusFrequencyHz: number;
  readOnly: boolean;
  showExtendedHigh: boolean;
  onCellsChange: (cells: Record<string, ThresholdCell>) => void;
  onActiveModeChange: (mode: ActivePlotMode) => void;
  onFocusFrequencyChange: (frequencyHz: number) => void;
  onToggleEar: () => void;
  onToggleMasked: () => void;
};

export function AudiogramGrid({
  frequencies,
  cells,
  activeMode,
  focusFrequencyHz,
  readOnly,
  showExtendedHigh,
  onCellsChange,
  onActiveModeChange,
  onFocusFrequencyChange,
  onToggleEar,
  onToggleMasked,
}: AudiogramGridProps) {
  const t = useTranslations("audiology");

  const rowIndex = useMemo(() => {
    return GRID_ROWS.findIndex(
      (row) =>
        row.ear === activeMode.ear &&
        row.conduction === activeMode.conduction &&
        row.isMasked === activeMode.isMasked,
    );
  }, [activeMode]);

  const moveFocus = useCallback(
    (deltaFreq: number, deltaRow: number) => {
      const nextRow =
        GRID_ROWS[(rowIndex + deltaRow + GRID_ROWS.length) % GRID_ROWS.length];
      onActiveModeChange({
        ear: nextRow.ear,
        conduction: nextRow.conduction,
        isMasked: nextRow.isMasked,
      });
      const rowFreqs = frequenciesForRow(nextRow.conduction, frequencies);
      const currentIndex = Math.max(0, rowFreqs.indexOf(focusFrequencyHz));
      const nextIndex = Math.min(
        rowFreqs.length - 1,
        Math.max(0, currentIndex + deltaFreq),
      );
      onFocusFrequencyChange(rowFreqs[nextIndex] ?? rowFreqs[0] ?? 1000);
    },
    [
      focusFrequencyHz,
      frequencies,
      onActiveModeChange,
      onFocusFrequencyChange,
      rowIndex,
    ],
  );

  const handleGridKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (readOnly) {
        return;
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        moveFocus(1, 0);
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        moveFocus(-1, 0);
      } else if (event.key === "ArrowDown") {
        event.preventDefault();
        moveFocus(0, 1);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        moveFocus(0, -1);
      } else if (event.key === "Tab") {
        event.preventDefault();
        onToggleEar();
      } else if (event.key === "m" || event.key === "M") {
        event.preventDefault();
        onToggleMasked();
      } else if (event.key === "n" || event.key === "N") {
        event.preventDefault();
        onCellsChange(toggleNoResponse(cells, activeMode, focusFrequencyHz));
      }
    },
    [
      activeMode,
      cells,
      focusFrequencyHz,
      moveFocus,
      onCellsChange,
      onToggleEar,
      onToggleMasked,
      readOnly,
    ],
  );

  return (
    <div
      dir="ltr"
      className="overflow-x-auto rounded-xl border border-border bg-card"
      tabIndex={0}
      onKeyDown={handleGridKeyDown}
      {...testIdProps(testIds.audiology.grid)}
    >
      <table className="min-w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/40">
            <th className="sticky start-0 z-10 bg-muted/40 px-3 py-2 text-start font-medium">
              {t("grid.series")}
            </th>
            {frequencies.map((hz) => (
              <th key={hz} className="px-2 py-2 text-center font-medium">
                {hz >= 1000 ? `${hz / 1000}k` : hz}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {GRID_ROWS.map((row) => (
            <tr key={`${row.ear}-${row.conduction}-${row.isMasked}`}>
              <th className="sticky start-0 z-10 bg-card px-3 py-1 text-start font-normal text-muted-foreground">
                {gridRowLabel(t, row.ear, row.conduction, row.isMasked)}
              </th>
              {frequencies.map((hz) => {
                if (
                  !frequencyAllowed(hz, row.conduction, showExtendedHigh) ||
                  (row.conduction === "bone" &&
                    !(BONE_FREQUENCIES_HZ as readonly number[]).includes(hz))
                ) {
                  return (
                    <td
                      key={hz}
                      className="bg-muted/20 px-1 py-1 text-center text-muted-foreground"
                    >
                      —
                    </td>
                  );
                }
                const key = cellKey(row.ear, row.conduction, row.isMasked, hz);
                const cell = cells[key];
                const focused =
                  row.ear === activeMode.ear &&
                  row.conduction === activeMode.conduction &&
                  row.isMasked === activeMode.isMasked &&
                  hz === focusFrequencyHz;
                return (
                  <td key={hz} className="px-1 py-1">
                    <input
                      type="number"
                      min={-10}
                      max={130}
                      step={5}
                      disabled={readOnly}
                      className={`h-9 w-14 rounded-md border px-1 text-center text-sm ${
                        focused
                          ? "border-primary ring-2 ring-primary/30"
                          : "border-input"
                      }`}
                      value={cell?.levelDb ?? ""}
                      onFocus={() => {
                        onActiveModeChange({
                          ear: row.ear,
                          conduction: row.conduction,
                          isMasked: row.isMasked,
                        });
                        onFocusFrequencyChange(hz);
                      }}
                      onChange={(event) => {
                        const raw = event.target.value.trim();
                        if (!raw) {
                          const next = { ...cells };
                          delete next[key];
                          onCellsChange(next);
                          return;
                        }
                        const levelDb = snapLevelDb(Number(raw));
                        onCellsChange(
                          setCellValue(
                            cells,
                            {
                              ear: row.ear,
                              conduction: row.conduction,
                              isMasked: row.isMasked,
                            },
                            hz,
                            levelDb,
                            cell?.isNoResponse ?? false,
                          ),
                        );
                      }}
                      {...testIdProps(
                        audiogramCellTestId(
                          row.ear,
                          row.conduction,
                          row.isMasked,
                          hz,
                        ),
                      )}
                    />
                    <button
                      type="button"
                      className={`mt-0.5 block w-full text-[10px] ${
                        cell?.isNoResponse
                          ? "font-semibold text-primary"
                          : "text-muted-foreground"
                      }`}
                      disabled={readOnly}
                      onClick={() =>
                        onCellsChange(
                          toggleNoResponse(
                            cells,
                            {
                              ear: row.ear,
                              conduction: row.conduction,
                              isMasked: row.isMasked,
                            },
                            hz,
                          ),
                        )
                      }
                      {...testIdProps(
                        audiogramNoResponseTestId(
                          row.ear,
                          row.conduction,
                          row.isMasked,
                          hz,
                        ),
                      )}
                    >
                      {t("grid.noResponseShort")}
                    </button>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function frequenciesForRow(
  conduction: "air" | "bone",
  frequencies: number[],
): number[] {
  if (conduction === "air") {
    return frequencies;
  }
  return frequencies.filter((hz) =>
    (BONE_FREQUENCIES_HZ as readonly number[]).includes(hz),
  );
}

export function cellValueAt(
  cells: Record<string, ThresholdCell>,
  mode: ActivePlotMode,
  frequencyHz: number,
): ThresholdCell | undefined {
  return cells[cellKey(mode.ear, mode.conduction, mode.isMasked, frequencyHz)];
}

export function applyPlotToCells(
  cells: Record<string, ThresholdCell>,
  mode: ActivePlotMode,
  frequencyHz: number,
  levelDb: number,
): Record<string, ThresholdCell> {
  return setCellValue(cells, mode, frequencyHz, levelDb, false);
}
