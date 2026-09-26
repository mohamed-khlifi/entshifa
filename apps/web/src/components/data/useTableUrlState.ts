'use client';

import { usePathname, useRouter } from '@/lib/i18n/navigation';
import { useSearchParams } from 'next/navigation';
import { useCallback, useMemo } from 'react';

export type TableSortDir = 'asc' | 'desc';

export type TableUrlState = {
  page: number;
  pageSize: number;
  sortBy: string | null;
  sortDir: TableSortDir;
  q: string;
  visibility: Record<string, boolean>;
};

const DEFAULT_PAGE_SIZE = 20;

function parseVisibility(raw: string | null): Record<string, boolean> {
  if (!raw) {
    return {};
  }
  const out: Record<string, boolean> = {};
  for (const part of raw.split(',')) {
    const id = part.trim();
    if (id.startsWith('-') && id.length > 1) {
      out[id.slice(1)] = false;
    } else if (id.length > 0) {
      out[id] = true;
    }
  }
  return out;
}

function serializeVisibility(visibility: Record<string, boolean>): string | null {
  const parts = Object.entries(visibility)
    .filter(([, visible]) => !visible)
    .map(([id]) => `-${id}`);
  return parts.length > 0 ? parts.join(',') : null;
}

export function useTableUrlState(options?: {
  defaultPageSize?: number;
  defaultSortBy?: string;
  defaultSortDir?: TableSortDir;
}): {
  state: TableUrlState;
  setState: (patch: Partial<TableUrlState>) => void;
} {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const defaultPageSize = options?.defaultPageSize ?? DEFAULT_PAGE_SIZE;

  const state = useMemo<TableUrlState>(() => {
    const page = Math.max(1, Number(searchParams.get('page') ?? '1') || 1);
    const pageSize = Math.max(
      1,
      Math.min(100, Number(searchParams.get('pageSize') ?? String(defaultPageSize)) || defaultPageSize),
    );
    const sortBy = searchParams.get('sortBy') ?? options?.defaultSortBy ?? null;
    const sortDirRaw = searchParams.get('sortDir');
    const sortDir: TableSortDir =
      sortDirRaw === 'desc' || sortDirRaw === 'asc'
        ? sortDirRaw
        : (options?.defaultSortDir ?? 'asc');
    const q = searchParams.get('q') ?? '';
    const visibility = parseVisibility(searchParams.get('cols'));
    return { page, pageSize, sortBy, sortDir, q, visibility };
  }, [defaultPageSize, options?.defaultSortBy, options?.defaultSortDir, searchParams]);

  const setState = useCallback(
    (patch: Partial<TableUrlState>) => {
      const next: TableUrlState = { ...state, ...patch };
      const params = new URLSearchParams(searchParams.toString());
      params.set('page', String(next.page));
      params.set('pageSize', String(next.pageSize));
      if (next.sortBy) {
        params.set('sortBy', next.sortBy);
        params.set('sortDir', next.sortDir);
      } else {
        params.delete('sortBy');
        params.delete('sortDir');
      }
      if (next.q) {
        params.set('q', next.q);
      } else {
        params.delete('q');
      }
      const cols = serializeVisibility(next.visibility);
      if (cols) {
        params.set('cols', cols);
      } else {
        params.delete('cols');
      }
      router.replace(`${pathname}?${params.toString()}`);
    },
    [pathname, router, searchParams, state],
  );

  return { state, setState };
}
