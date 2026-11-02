import type { useTranslations } from "next-intl";

type AudiogramT = ReturnType<typeof useTranslations<"audiology">>;

export function transducerLabel(t: AudiogramT, value: string): string {
  return t(`transducer.${value}` as "transducer.headphones");
}

export function methodLabel(t: AudiogramT, value: string): string {
  return t(`method.${value}` as "method.standard");
}

export function reliabilityLabel(t: AudiogramT, value: string): string {
  return t(`reliability.${value}` as "reliability.good");
}

export function earLabel(t: AudiogramT, value: string): string {
  return t(`ear.${value}` as "ear.right");
}

export function conductionLabel(t: AudiogramT, value: string): string {
  return t(`conduction.${value}` as "conduction.air");
}

export function gridRowLabel(
  t: AudiogramT,
  ear: string,
  conduction: string,
  isMasked: boolean,
): string {
  const mask = isMasked ? t("grid.masked") : t("grid.unmasked");
  return `${earLabel(t, ear)} · ${conductionLabel(t, conduction)} · ${mask}`;
}

export function formatFrequencyHz(frequencyHz: number): string {
  if (frequencyHz >= 1000) {
    const khz = frequencyHz / 1000;
    return Number.isInteger(khz) ? `${khz} kHz` : `${khz} kHz`;
  }
  return `${frequencyHz} Hz`;
}

export function ptaFormulaLabel(t: AudiogramT, code: string | null): string {
  if (!code) {
    return t("metrics.formulaUnknown");
  }
  return t(`ptaFormula.${code}` as "ptaFormula.3freq");
}
