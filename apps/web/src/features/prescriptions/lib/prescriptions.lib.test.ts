import { describe, expect, it } from "vitest";

import {
  emptyItem,
  itemFromTemplate,
  itemWrite,
  readStoredTaper,
} from "./items";
import { hasUnresolvedBlock, placeAlerts } from "./safety";
import { paperLocale, scheduleDoses } from "./display";
import type { CalculationRead, SafetyAlertRead } from "@/lib/api/generated";

const FORMULARY = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

describe("itemWrite", () => {
  it("accepts a formulary dose and keeps the decimal as text", () => {
    const item = emptyItem("row");
    item.formularyEntryPublicId = FORMULARY;
    item.doseAmount = "400";
    item.doseUnit = "mg";
    const write = itemWrite(item, 0);
    expect(write?.doseAmount).toBe("400");
    expect(write?.formularyEntryPublicId).toBe(FORMULARY);
    expect(write?.freeTextName).toBeNull();
  });

  it("rejects an item that is both formulary and free text", () => {
    const item = emptyItem("row");
    item.formularyEntryPublicId = FORMULARY;
    item.freeTextName = "Compounded drops";
    item.doseAmount = "1";
    item.doseUnit = "mg";
    expect(itemWrite(item, 0)).toBeNull();
  });
});

describe("itemFromTemplate", () => {
  it("copies a saved line into an editable draft", () => {
    const draft = itemFromTemplate(
      {
        formularyEntryPublicId: FORMULARY,
        route: "nasal",
        frequencyPerDay: 2,
        durationDays: 14,
        instructionsText: "Aim away from the septum.",
        calculateFromFormulary: false,
        doseAmount: "1",
        doseUnit: "spray",
      },
      "copy",
    );
    expect(draft?.route).toBe("nasal");
    expect(draft?.instructionsText).toBe("Aim away from the septum.");
    expect(draft?.formularyEntryPublicId).toBe(FORMULARY);
  });
});

describe("readStoredTaper", () => {
  it("reads the clinic taper without changing the numbers", () => {
    expect(
      readStoredTaper({
        taper: {
          start_mg: "60",
          step_mg: "10",
          days_per_step: 2,
          minimum_mg: "10",
        },
      }),
    ).toEqual({
      startMg: "60",
      stepMg: "10",
      daysPerStep: "2",
      minimumMg: "10",
    });
  });
});

describe("safety blocks", () => {
  it("keeps a pediatric weight block even when an override is typed", () => {
    const item = emptyItem("row");
    item.allergyOverride = "Clinical need";
    const alerts: SafetyAlertRead[] = [
      {
        code: "prescription.pediatric_weight_missing",
        severity: "block",
        itemIndex: null,
      },
    ];
    const placed = placeAlerts(alerts, [item.key]);
    expect(hasUnresolvedBlock(placed, new Map([[item.key, item]]))).toBe(true);
  });

  it("accepts an allergy override reason before issue", () => {
    const item = emptyItem("row");
    item.allergyOverride = "No alternative in the formulary";
    const alerts: SafetyAlertRead[] = [
      {
        code: "prescription.allergy_conflict",
        severity: "block",
        itemIndex: 0,
      },
    ];
    const placed = placeAlerts(alerts, [item.key]);
    expect(hasUnresolvedBlock(placed, new Map([[item.key, item]]))).toBe(false);
  });
});

describe("server calculation display", () => {
  it("splits the taper schedule the engine returned", () => {
    const calculation = {
      code: "prescriptions.steroid_taper",
      value: "4",
      unit: "day",
      formula: "schedule",
      version: "1.0.0",
      reference: "caller",
      inputs: {},
      flags: [{ code: "schedule_mg", detail: { days: "60,60,50,50" } }],
    } satisfies CalculationRead;
    expect(scheduleDoses(calculation)).toEqual(["60", "60", "50", "50"]);
  });

  it("prints in the patient language when that locale is supported", () => {
    expect(paperLocale("fr", "en")).toBe("fr");
    expect(paperLocale("de", "ar")).toBe("ar");
    expect(paperLocale("de", "es")).toBe("en");
  });
});
