import { defineRouting } from 'next-intl/routing';

import { DEFAULT_LOCALE, LOCALES, type AppLocale } from '@/lib/i18n/config';

export const routing = defineRouting({
  locales: [...LOCALES],
  defaultLocale: DEFAULT_LOCALE,
  localePrefix: 'always',
});

export type { AppLocale };
