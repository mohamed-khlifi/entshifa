import { getRequestConfig } from 'next-intl/server';

import { routing, type AppLocale } from './routing';

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;
  if (!locale || !routing.locales.includes(locale as AppLocale)) {
    locale = routing.defaultLocale;
  }

  const [common, auth, errors] = await Promise.all([
    import(`../../messages/${locale}/common.json`),
    import(`../../messages/${locale}/auth.json`),
    import(`../../messages/${locale}/errors.json`),
  ]);

  return {
    locale,
    messages: {
      common: common.default,
      auth: auth.default,
      errors: errors.default,
    },
  };
});
