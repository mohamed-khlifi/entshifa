import { ONLY_HEARING_EAR } from "../constants";
import type { PatientFlagRead } from "@/lib/api/generated";

export function localIsoDate(value: Date = new Date()): string {
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${value.getFullYear()}-${month}-${day}`;
}

export function isFlagActive(
  flag: Pick<PatientFlagRead, "endedOn">,
  today: Date = new Date(),
): boolean {
  if (!flag.endedOn) {
    return true;
  }
  return flag.endedOn > localIsoDate(today);
}

export function activeFlags(
  flags: readonly PatientFlagRead[],
  today: Date = new Date(),
): PatientFlagRead[] {
  return flags.filter((flag) => isFlagActive(flag, today));
}

export function splitHearingAlerts(flags: readonly PatientFlagRead[]): {
  onlyHearingEar: PatientFlagRead[];
  other: PatientFlagRead[];
} {
  const current = activeFlags(flags);
  return {
    onlyHearingEar: current.filter(
      (flag) => flag.flagCode === ONLY_HEARING_EAR,
    ),
    other: current.filter((flag) => flag.flagCode !== ONLY_HEARING_EAR),
  };
}
