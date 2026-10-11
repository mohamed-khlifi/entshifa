import type { useTranslations } from "next-intl";

type OtologyTranslator = ReturnType<typeof useTranslations<"otology">>;

export function methodLabel(t: OtologyTranslator, value: string): string {
  return value === "otoscopy" ? t("method.otoscopy") : t("method.microscopy");
}

export function lateralityLabel(t: OtologyTranslator, value: string): string {
  switch (value) {
    case "right":
      return t("laterality.right");
    case "left":
      return t("laterality.left");
    default:
      return t("laterality.bilateral");
  }
}

export function drugLabel(t: OtologyTranslator, code: string): string {
  switch (code) {
    case "DRUG.IT.METHYLPREDNISOLONE":
      return t("drug.methylprednisolone");
    case "DRUG.IT.GENTAMICIN":
      return t("drug.gentamicin");
    default:
      return t("drug.dexamethasone");
  }
}

export function optionLabel(
  t: OtologyTranslator,
  group: string,
  value: string,
): string {
  const key = value ? `${group}.${value}` : `${group}.none`;
  if (t.has(key as "weber.none")) {
    return t(key as "weber.midline");
  }
  return value;
}
