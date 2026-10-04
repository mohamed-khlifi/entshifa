"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api/errors";
import type { AutosaveStatus } from "@/lib/forms/autosave";
import {
  AUTOSAVE_DEFAULT_DELAY_MS,
  AUTOSAVE_DEFAULT_MAX_WAIT_MS,
  writeDraftSnapshot,
} from "@/lib/forms/autosave";

import type { EncounterRead } from "@/lib/api/generated";

import { patchEncounter } from "../api/encounters.api";
import {
  diffEncounterPatch,
  type EncounterFieldSnapshot,
} from "../lib/encounter-patch";
import { draftKey } from "../lib/hydration";

export type AutosaveConflict = {
  serverVersion: number;
  clientVersion: number;
};

type Scope = { locale: string; clinicPublicId: string };

export function useEncounterAutosave(options: {
  encounterId: string | null;
  version: number;
  enabled: boolean;
  scope: Scope;
  serverSnapshot: EncounterFieldSnapshot | null;
  currentSnapshot: EncounterFieldSnapshot | null;
  draft: unknown;
  resetToken: number;
  onVersion: (version: number) => void;
  onSaved?: (encounter: EncounterRead) => void;
}) {
  const [status, setStatus] = useState<AutosaveStatus>("idle");
  const [conflict, setConflict] = useState<AutosaveConflict | null>(null);
  const baselineRef = useRef<EncounterFieldSnapshot | null>(null);
  const versionRef = useRef(options.version);
  const firstDirtyRef = useRef<number | null>(null);
  const currentRef = useRef(options.currentSnapshot);
  const scopeRef = useRef(options.scope);
  const enabledRef = useRef(options.enabled);
  const encounterIdRef = useRef(options.encounterId);
  const onVersionRef = useRef(options.onVersion);
  const onSavedRef = useRef(options.onSaved);
  currentRef.current = options.currentSnapshot;
  scopeRef.current = options.scope;
  versionRef.current = options.version;
  enabledRef.current = options.enabled;
  encounterIdRef.current = options.encounterId;
  onVersionRef.current = options.onVersion;
  onSavedRef.current = options.onSaved;

  const serverReady = options.serverSnapshot !== null;
  const serverSnapshotRef = useRef(options.serverSnapshot);
  serverSnapshotRef.current = options.serverSnapshot;
  useEffect(() => {
    baselineRef.current = serverSnapshotRef.current;
    firstDirtyRef.current = null;
    setConflict(null);
    setStatus("idle");
  }, [options.encounterId, options.resetToken, serverReady]);

  useEffect(() => {
    if (!options.encounterId || options.draft === null) {
      return;
    }
    void writeDraftSnapshot(draftKey(options.encounterId), options.draft).catch(
      () => undefined,
    );
  }, [options.draft, options.encounterId]);

  const flush = useCallback(async (): Promise<EncounterRead | undefined> => {
    const encounterId = encounterIdRef.current;
    const baseline = baselineRef.current;
    const current = currentRef.current;
    if (!encounterId || !baseline || !current || !enabledRef.current) {
      return undefined;
    }
    const body = diffEncounterPatch(versionRef.current, baseline, current);
    if (!body) {
      setStatus((value) => (value === "conflict" ? value : "idle"));
      return undefined;
    }
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      setStatus("offline");
      return undefined;
    }
    setStatus("saving");
    try {
      const saved = await patchEncounter(encounterId, body, scopeRef.current);
      baselineRef.current = current;
      versionRef.current = saved.version;
      firstDirtyRef.current = null;
      onVersionRef.current(saved.version);
      onSavedRef.current?.(saved);
      setStatus("saved");
      return saved;
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        const serverVersion = Number(error.context.serverVersion);
        const clientVersion = Number(error.context.clientVersion);
        setConflict({
          serverVersion: Number.isFinite(serverVersion) ? serverVersion : 0,
          clientVersion: Number.isFinite(clientVersion)
            ? clientVersion
            : versionRef.current,
        });
        setStatus("conflict");
        return undefined;
      }
      setStatus("error");
      return undefined;
    }
  }, []);

  const snapshotKey = JSON.stringify(options.currentSnapshot);
  useEffect(() => {
    if (!options.enabled || !options.currentSnapshot || !baselineRef.current) {
      return;
    }
    const body = diffEncounterPatch(
      versionRef.current,
      baselineRef.current,
      options.currentSnapshot,
    );
    if (!body) {
      return;
    }
    const now = Date.now();
    firstDirtyRef.current ??= now;
    const elapsed = now - (firstDirtyRef.current ?? now);
    const wait = Math.min(
      AUTOSAVE_DEFAULT_DELAY_MS,
      Math.max(0, AUTOSAVE_DEFAULT_MAX_WAIT_MS - elapsed),
    );
    const timer = window.setTimeout(() => {
      void flush();
    }, wait);
    return () => window.clearTimeout(timer);
  }, [flush, options.currentSnapshot, options.enabled, snapshotKey]);

  useEffect(() => {
    const onOnline = () => {
      void flush();
    };
    const onOffline = () => setStatus("offline");
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, [flush]);

  return { status, conflict, flush };
}
