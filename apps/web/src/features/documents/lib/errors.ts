import type { useTranslations } from "next-intl";

import { ApiError } from "@/lib/api/errors";

type ErrorsT = ReturnType<typeof useTranslations<"errors">>;

export function documentErrorText(t: ErrorsT, error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === "documents.undeclared_placeholder") {
      return t("documents.undeclared_placeholder");
    }
    if (error.code === "documents.template_syntax") {
      return t("documents.template_syntax");
    }
    if (error.code === "documents.immutable") {
      return t("documents.immutable");
    }
    if (error.code === "documents.not_rendered") {
      return t("documents.not_rendered");
    }
    if (error.code === "documents.encounter_required") {
      return t("documents.encounter_required");
    }
    if (error.code === "documents.payload_invalid") {
      return t("documents.payload_invalid");
    }
    if (error.code === "documents.absence_range") {
      return t("documents.absence_range");
    }
    if (error.code === "documents.mri_implant_blocked") {
      return t("documents.mri_implant_blocked");
    }
  }
  return t("generic");
}
