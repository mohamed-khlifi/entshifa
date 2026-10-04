import type { EncounterRead } from "@/lib/api/generated";

export function selectCopySource(
  encounters: readonly EncounterRead[],
  activePublicId: string | null,
): EncounterRead | null {
  const active =
    encounters.find((row) => row.publicId === activePublicId) ?? null;
  if (active && active.status !== "draft") {
    return active;
  }
  return encounters.find((row) => row.publicId !== active?.publicId) ?? null;
}
