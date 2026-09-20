'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import { useState, type ReactNode } from 'react';
import { Toaster } from 'sonner';

import { createQueryClient } from '@/lib/api/query-client';

import { PermissionProvider } from './permission-provider';
import { SessionProvider, useSession } from './session-provider';

function PermissionBridge({ children }: { children: ReactNode }) {
  const { session } = useSession();
  return (
    <PermissionProvider permissions={session?.permissions ?? []}>
      {children}
    </PermissionProvider>
  );
}

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => createQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" forcedTheme="light" enableSystem={false}>
        <SessionProvider>
          <PermissionBridge>{children}</PermissionBridge>
        </SessionProvider>
        <Toaster richColors closeButton />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
