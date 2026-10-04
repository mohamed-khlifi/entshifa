export const RED_FLAG_IDS = [
  "dysphagiaWeightLoss",
  "facialWeaknessParotid",
  "hoarsenessSmoker",
  "neckLumpAdult",
  "stridor",
  "suddenHearingLoss",
  "unilateralObstructionBleeding",
  "unilateralTinnitus",
] as const;

export type RedFlagId = (typeof RED_FLAG_IDS)[number];

const SUGGESTED_BY_COMPLAINT: Record<string, readonly RedFlagId[]> = {
  "CC.EPISTAXIS": ["unilateralObstructionBleeding"],
  "CC.HEARING_LOSS": ["suddenHearingLoss"],
  "CC.HOARSENESS": ["hoarsenessSmoker", "dysphagiaWeightLoss"],
  "CC.NASAL_OBSTRUCTION": ["unilateralObstructionBleeding"],
  "CC.TINNITUS": ["unilateralTinnitus"],
};

export function suggestedRedFlags(
  complaintCodes: readonly string[],
): RedFlagId[] {
  const flags = new Set<RedFlagId>();
  for (const code of complaintCodes) {
    for (const flag of SUGGESTED_BY_COMPLAINT[code] ?? []) {
      flags.add(flag);
    }
  }
  return RED_FLAG_IDS.filter((flag) => flags.has(flag));
}

export function toggleRedFlag(
  confirmed: readonly RedFlagId[],
  flag: RedFlagId,
): RedFlagId[] {
  return confirmed.includes(flag)
    ? confirmed.filter((item) => item !== flag)
    : [...confirmed, flag];
}
