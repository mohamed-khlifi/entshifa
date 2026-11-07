import { NextIntlClientProvider } from "next-intl";
import { getMessages, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import { hasLocale } from "next-intl";
import type { ReactNode } from "react";

import { routing } from "@/lib/i18n/routing";
import { getLocaleDirection, usesArabicFont } from "@/lib/i18n/config";
import { AppProviders } from "@/providers/app-providers";
import { fontArabic, fontSans } from "@/lib/fonts";
import { cn } from "@/lib/utils/cn";

type Props = {
  children: ReactNode;
  params: Promise<{ locale: string }>;
};

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({ children, params }: Props) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  setRequestLocale(locale);
  const messages = await getMessages();
  const direction = getLocaleDirection(locale);
  const fontVariables = usesArabicFont(locale)
    ? cn(fontSans.variable, fontArabic.variable)
    : fontSans.variable;

  return (
    <html lang={locale} dir={direction} suppressHydrationWarning>
      <body
        className={cn(
          fontVariables,
          "min-h-screen bg-background font-sans text-foreground antialiased",
          usesArabicFont(locale) && "font-arabic",
        )}
      >
        <NextIntlClientProvider messages={messages}>
          <AppProviders>{children}</AppProviders>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
