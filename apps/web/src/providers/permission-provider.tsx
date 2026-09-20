'use client';

import { createContext, useContext, useMemo, type ReactNode } from 'react';

type PermissionContextValue = {
  permissions: ReadonlySet<string>;
  can: (permission: string) => boolean;
};

const PermissionContext = createContext<PermissionContextValue | null>(null);

export function PermissionProvider({
  permissions,
  children,
}: {
  permissions: readonly string[];
  children: ReactNode;
}) {
  const value = useMemo<PermissionContextValue>(
    () => ({
      permissions: new Set(permissions),
      can: (permission: string) => permissions.includes(permission),
    }),
    [permissions],
  );
  return (
    <PermissionContext.Provider value={value}>{children}</PermissionContext.Provider>
  );
}

export function usePermission(permission: string): boolean {
  const context = useContext(PermissionContext);
  if (context === null) {
    return false;
  }
  return context.can(permission);
}

export function usePermissions(): PermissionContextValue {
  const context = useContext(PermissionContext);
  if (context === null) {
    throw new Error('usePermissions requires PermissionProvider');
  }
  return context;
}

export function Can({
  permission,
  children,
  fallback = null,
}: {
  permission: string;
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const allowed = usePermission(permission);
  return allowed ? children : fallback;
}
