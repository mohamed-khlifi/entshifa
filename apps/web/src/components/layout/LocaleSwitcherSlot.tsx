"use client";

import type { ReactNode } from "react";

import { LocaleSwitcher } from "@/components/layout/LocaleSwitcher";

type LocaleSwitcherSlotProps = {
  children: ReactNode;
};

/** Fixed top-end locale control on routes without the app topbar (e.g. login). */
export function LocaleSwitcherSlot({ children }: LocaleSwitcherSlotProps) {
  return (
    <div className="relative min-h-screen">
      <div className="pointer-events-none absolute inset-x-0 top-0 z-20 flex justify-end p-4 sm:p-6">
        <div className="pointer-events-auto">
          <LocaleSwitcher />
        </div>
      </div>
      {children}
    </div>
  );
}
