import { defineRouting } from 'next-intl/routing';

import {
  DEFAULT_LOCALE,
  getEnabledLocales,
  type AppLocale,
} from '@/lib/i18n/config';

export const routing = defineRouting({
  locales: [...getEnabledLocales()],
  defaultLocale: DEFAULT_LOCALE,
  localePrefix: 'always',
});

export type { AppLocale };
