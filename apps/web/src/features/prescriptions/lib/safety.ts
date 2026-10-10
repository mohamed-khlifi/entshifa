import type { SafetyAlertRead } from "@/lib/api/generated";

import { ALLERGY_OVERRIDE, DOSE_OVERRIDE, WEIGHT_BLOCK } from "../constants";
import type { ItemValues } from "./items";

export type PlacedAlert = SafetyAlertRead & {
  itemKey: string | null;
};

export function placeAlerts(
  alerts: readonly SafetyAlertRead[],
  itemKeys: readonly string[],
): PlacedAlert[] {
  return alerts.map((alert) => ({
    ...alert,
    itemKey:
      alert.itemIndex == null ? null : (itemKeys[alert.itemIndex] ?? null),
  }));
}

function overrideReason(item: ItemValues, code: string): string {
  if (code === ALLERGY_OVERRIDE) {
    return item.allergyOverride.trim();
  }
  if (code === DOSE_OVERRIDE) {
    return item.doseOverride.trim();
  }
  return "";
}

export function isUnresolvedBlock(
  alert: PlacedAlert,
  items: ReadonlyMap<string, ItemValues>,
): boolean {
  if (alert.severity !== "block") {
    return false;
  }
  if (alert.code === WEIGHT_BLOCK || alert.itemKey == null) {
    return true;
  }
  if (alert.code !== ALLERGY_OVERRIDE && alert.code !== DOSE_OVERRIDE) {
    return true;
  }
  const item = items.get(alert.itemKey);
  if (!item) {
    return true;
  }
  return overrideReason(item, alert.code).length === 0;
}

export function hasUnresolvedBlock(
  alerts: readonly PlacedAlert[],
  items: ReadonlyMap<string, ItemValues>,
): boolean {
  return alerts.some((alert) => isUnresolvedBlock(alert, items));
}
