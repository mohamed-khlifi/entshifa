import { getRequestConfig } from "next-intl/server";

import {
  DEFAULT_LOCALE,
  MESSAGE_NAMESPACES,
  isAppLocale,
  type MessageNamespace,
} from "@/lib/i18n/config";

type MessageTree = Record<string, unknown>;

async function loadNamespace(
  locale: string,
  namespace: MessageNamespace,
): Promise<MessageTree> {
  // Canonical catalogs live in packages/i18n-messages (architecture §4 / P0-11).
  const catalog = await import(
    `../../../../../packages/i18n-messages/${locale}/${namespace}.json`
  );
  return catalog.default as MessageTree;
}

async function loadMessages(
  locale: string,
): Promise<Record<MessageNamespace, MessageTree>> {
  const entries = await Promise.all(
    MESSAGE_NAMESPACES.map(async (namespace) => {
      const tree = await loadNamespace(locale, namespace);
      return [namespace, tree] as const;
    }),
  );
  return Object.fromEntries(entries) as Record<MessageNamespace, MessageTree>;
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
