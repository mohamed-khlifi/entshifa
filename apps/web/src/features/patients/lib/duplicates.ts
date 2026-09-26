import { ApiError } from "@/lib/api/errors";

export function duplicateCandidateIds(error: unknown): string[] | null {
  if (
    !(error instanceof ApiError) ||
    error.code !== "patient.possible_duplicate"
  ) {
    return null;
  }
  const raw = error.context.candidates;
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw.filter((item): item is string => typeof item === "string");
}
