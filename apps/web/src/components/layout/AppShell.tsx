'use client';

import type { ReactNode } from 'react';

import { testIdProps, testIds } from '@/lib/test/test-id';

import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div
      className="flex min-h-screen flex-col bg-muted/30"
      {...testIdProps(testIds.layout.shell)}
    >
      <Topbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 overflow-auto p-6" {...testIdProps(testIds.layout.main)}>
          {children}
        </main>
      </div>
    </div>
  );
}
