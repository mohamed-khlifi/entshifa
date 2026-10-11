import type { useTranslations } from "next-intl";

type OfficeTranslator = ReturnType<typeof useTranslations<"officeProcedures">>;

export function optionLabel(
  t: OfficeTranslator,
  group: string,
  value: string,
): string {
  const key = `${group}.${value}` as "subtype.epistaxis_management";
  if (value && t.has(key)) {
    return t(key);
  }
  return value;
}

export function recordStatusLabel(t: OfficeTranslator, status: string): string {
  switch (status) {
    case "signed":
      return t("recordStatus.signed");
    case "amended":
      return t("recordStatus.amended");
    default:
      return t("recordStatus.draft");
  }
}
