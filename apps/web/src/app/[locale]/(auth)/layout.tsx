import type { ReactNode } from "react";

import { LocaleSwitcherSlot } from "@/components/layout/LocaleSwitcherSlot";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return <LocaleSwitcherSlot>{children}</LocaleSwitcherSlot>;
}
