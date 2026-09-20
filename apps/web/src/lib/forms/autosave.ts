export type AutosaveStatus =
  | 'idle'
  | 'saving'
  | 'saved'
  | 'offline'
  | 'conflict'
  | 'error';

export type AutosaveConfig<TValues extends Record<string, unknown>> = {
  /** Draft key for IndexedDB (e.g. encounter public id). */
  key: string;
  delayMs?: number;
  maxWaitMs?: number;
  /** Current server version for optimistic concurrency. */
  version: number;
  onSave: (payload: {
    values: Partial<TValues>;
    version: number;
  }) => Promise<{ version: number }>;
  onConflict?: (payload: {
    local: Partial<TValues>;
    serverVersion: number;
  }) => void;
};

export const AUTOSAVE_DEFAULT_DELAY_MS = 2000;
export const AUTOSAVE_DEFAULT_MAX_WAIT_MS = 15000;

const DRAFT_DB = 'entshifa-drafts';
const DRAFT_STORE = 'drafts';

function openDraftDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DRAFT_DB, 1);
    request.onerror = () => reject(request.error ?? new Error('indexedDB open failed'));
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(DRAFT_STORE)) {
        db.createObjectStore(DRAFT_STORE, { keyPath: 'key' });
      }
    };
  });
}

export async function writeDraftSnapshot<T>(
  key: string,
  values: T,
): Promise<void> {
  if (typeof indexedDB === 'undefined') {
    return;
  }
  const db = await openDraftDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(DRAFT_STORE, 'readwrite');
    tx.objectStore(DRAFT_STORE).put({
      key,
      values,
      updatedAt: Date.now(),
    });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error('draft write failed'));
  });
  db.close();
}

export async function readDraftSnapshot<T>(key: string): Promise<T | null> {
  if (typeof indexedDB === 'undefined') {
    return null;
  }
  const db = await openDraftDb();
  const result = await new Promise<T | null>((resolve, reject) => {
    const tx = db.transaction(DRAFT_STORE, 'readonly');
    const request = tx.objectStore(DRAFT_STORE).get(key);
    request.onsuccess = () => {
      const row = request.result as { values: T } | undefined;
      resolve(row?.values ?? null);
    };
    request.onerror = () => reject(request.error ?? new Error('draft read failed'));
  });
  db.close();
  return result;
}

export async function clearDraftSnapshot(key: string): Promise<void> {
  if (typeof indexedDB === 'undefined') {
    return;
  }
  const db = await openDraftDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(DRAFT_STORE, 'readwrite');
    tx.objectStore(DRAFT_STORE).delete(key);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error('draft clear failed'));
  });
  db.close();
}

/** Pure helper: pick only dirty keys from current values. */
export function pickDirtyValues<T extends Record<string, unknown>>(
  values: T,
  dirtyFields: Partial<Record<keyof T, unknown>>,
): Partial<T> {
  const out: Partial<T> = {};
  for (const key of Object.keys(dirtyFields) as (keyof T)[]) {
    if (dirtyFields[key]) {
      out[key] = values[key];
    }
  }
  return out;
}
