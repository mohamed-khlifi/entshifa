export const PLAN_KINDS = [
  "advice",
  "certificate",
  "follow_up",
  "imaging_requested",
  "medication",
  "procedure_today",
  "referral",
  "sick_leave",
  "surgery_proposed",
  "test_requested",
] as const;

export type PlanKind = (typeof PLAN_KINDS)[number];

export type PlanItemDraft = {
  id: string;
  kind: PlanKind;
  detail: string;
  source?: string;
};

export function toggleSuggestion(
  items: readonly PlanItemDraft[],
  source: string,
  kind: PlanKind,
  detail: string,
  id: string,
): PlanItemDraft[] {
  if (items.some((item) => item.source === source)) {
    return items.filter((item) => item.source !== source);
  }
  return [...items, { id, kind, detail, source }];
}

export function removePlanItem(
  items: readonly PlanItemDraft[],
  id: string,
): PlanItemDraft[] {
  return items.filter((item) => item.id !== id);
}
