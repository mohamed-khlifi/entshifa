import type { useTranslations } from "next-intl";

export function examinationRegionLabel(
  t: ReturnType<typeof useTranslations<"examination">>,
  labelKey: string,
): string {
  switch (labelKey) {
    case "tm.regions.canal":
      return t("tm.regions.canal");
    case "tm.regions.parsFlaccida":
      return t("tm.regions.parsFlaccida");
    case "tm.regions.anteroSuperior":
      return t("tm.regions.anteroSuperior");
    case "tm.regions.anteroInferior":
      return t("tm.regions.anteroInferior");
    case "tm.regions.posteroSuperior":
      return t("tm.regions.posteroSuperior");
    case "tm.regions.posteroInferior":
      return t("tm.regions.posteroInferior");
    case "nose.regions.vestibule":
      return t("nose.regions.vestibule");
    case "nose.regions.valve":
      return t("nose.regions.valve");
    case "nose.regions.septum":
      return t("nose.regions.septum");
    case "nose.regions.inferiorTurbinate":
      return t("nose.regions.inferiorTurbinate");
    case "nose.regions.middleTurbinate":
      return t("nose.regions.middleTurbinate");
    case "nose.regions.mucosa":
      return t("nose.regions.mucosa");
    case "oral.regions.lips":
      return t("oral.regions.lips");
    case "oral.regions.tongue":
      return t("oral.regions.tongue");
    case "oral.regions.softPalate":
      return t("oral.regions.softPalate");
    case "oral.regions.tonsil":
      return t("oral.regions.tonsil");
    case "oral.regions.posteriorWall":
      return t("oral.regions.posteriorWall");
    case "neck.regions.parotid":
      return t("neck.regions.parotid");
    case "neck.regions.levelIa":
      return t("neck.regions.levelIa");
    case "neck.regions.levelIb":
      return t("neck.regions.levelIb");
    case "neck.regions.levelIia":
      return t("neck.regions.levelIia");
    case "neck.regions.levelIib":
      return t("neck.regions.levelIib");
    case "neck.regions.submandibular":
      return t("neck.regions.submandibular");
    case "neck.regions.levelIii":
      return t("neck.regions.levelIii");
    case "neck.regions.levelIv":
      return t("neck.regions.levelIv");
    case "neck.regions.levelVa":
      return t("neck.regions.levelVa");
    case "neck.regions.levelVb":
      return t("neck.regions.levelVb");
    case "neck.regions.levelVi":
      return t("neck.regions.levelVi");
    case "neck.regions.thyroidLobe":
      return t("neck.regions.thyroidLobe");
    case "neck.regions.isthmus":
      return t("neck.regions.isthmus");
    case "neck.regions.levelVii":
      return t("neck.regions.levelVii");
    default:
      return t("regions.unknown");
  }
}

export function examinationMapTitle(
  t: ReturnType<typeof useTranslations<"examination">>,
  titleKey: string,
): string {
  switch (titleKey) {
    case "maps.tympanicMembrane":
      return t("maps.tympanicMembrane");
    case "maps.nasalCavity":
      return t("maps.nasalCavity");
    case "maps.oralCavity":
      return t("maps.oralCavity");
    case "maps.neckLevels":
      return t("maps.neckLevels");
    default:
      return t("regions.unknown");
  }
}
