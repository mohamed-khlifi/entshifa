'use client';

import type { ReactNode } from 'react';

import { testIdProps, testIds } from '@/lib/test/test-id';

import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

type AppShellProps = {
  children: ReactNode;
};

/**
 * Fixed chrome: topbar + sidebar stay put; only main content scrolls.
 */
export function AppShell({ children }: AppShellProps) {
  return (
    <div
      className="flex h-svh flex-col overflow-hidden bg-muted/30"
      {...testIdProps(testIds.layout.shell)}
    >
      <Topbar />
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <main
          className="min-h-0 min-w-0 flex-1 overflow-y-auto overscroll-contain p-6"
          {...testIdProps(testIds.layout.main)}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
