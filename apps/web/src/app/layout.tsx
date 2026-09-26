import type { ReactNode } from "react";

import "@/styles/globals.css";

/**
 * Root layout is a passthrough. `<html>` / `<body>` live in `[locale]/layout`
 * so `lang` and `dir` are set from the URL locale on the server (RTL without FOUC).
 */
export default function RootLayout({ children }: { children: ReactNode }) {
  return children;
}
