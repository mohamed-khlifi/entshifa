import { getRequestConfig } from 'next-intl/server';

import {
  DEFAULT_LOCALE,
  MESSAGE_NAMESPACES,
  PSEUDO_LOCALE,
  getLocaleDefinition,
  isAppLocale,
  type MessageNamespace,
} from '@/lib/i18n/config';
import { toPseudoLocaleMessages } from '@/lib/i18n/pseudo';

type MessageTree = Record<string, unknown>;

async function loadNamespace(
  catalogLocale: string,
  namespace: MessageNamespace,
): Promise<MessageTree> {
  const module = await import(
    `../../../../packages/i18n-messages/${catalogLocale}/${namespace}.json`
  );
  return module.default as MessageTree;
}

async function loadMessages(locale: string): Promise<Record<MessageNamespace, MessageTree>> {
  const definition = getLocaleDefinition(locale);
  const entries = await Promise.all(
    MESSAGE_NAMESPACES.map(async (namespace) => {
      const tree = await loadNamespace(definition.catalogLocale, namespace);
      return [namespace, tree] as const;
    }),
  );
  const messages = Object.fromEntries(entries) as Record<MessageNamespace, MessageTree>;
  if (locale === PSEUDO_LOCALE) {
    return toPseudoLocaleMessages(messages);
  }
  return messages;
}

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;
  if (!locale || !isAppLocale(locale)) {
    locale = DEFAULT_LOCALE;
  }

  return {
    locale,
    messages: await loadMessages(locale),
  };
});
