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
  }
  return t("generic");
}
