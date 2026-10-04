export type CockpitDraftEnvelope<T> = {
  baseVersion: number;
  state: T;
};

export function resolveHydration<T>(
  draft: CockpitDraftEnvelope<T> | null,
  serverVersion: number,
): { source: "draft" | "server"; conflict: boolean; state: T | null } {
  if (!draft) {
    return { source: "server", conflict: false, state: null };
  }
  return {
    source: "draft",
    conflict: draft.baseVersion !== serverVersion,
    state: draft.state,
  };
}

export function draftKey(encounterPublicId: string): string {
  return `encounter:${encounterPublicId}`;
}
