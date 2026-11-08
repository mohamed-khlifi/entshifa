import type { useTranslations } from "next-intl";

export function calculatorMessageKey(labelKey: string): string {
  return labelKey.startsWith("calculators.")
    ? labelKey.slice("calculators.".length)
    : labelKey;
}

export function calculatorCatalogKey(code: string): string {
  return `catalog.${code.replaceAll(".", "_")}`;
}

export function calculatorTitle(
  t: ReturnType<typeof useTranslations<"calculators">>,
  code: string,
): string {
  const key = calculatorCatalogKey(code);
  if (t.has(key)) {
    return t(key);
  }
  return code;
}
