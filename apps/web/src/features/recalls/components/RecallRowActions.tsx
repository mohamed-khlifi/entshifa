"use client";

import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import type { RecallRead } from "@/lib/api/generated";
import { recallActionTestId, testIdProps } from "@/lib/test/test-id";

export function RecallRowActions({
  recall,
  disabled,
  onBook,
  onContact,
  onUnreachable,
  onCancel,
}: {
  recall: RecallRead;
  disabled: boolean;
  onBook: (recall: RecallRead) => void;
  onContact: (
    recall: RecallRead,
    action: "call" | "sms" | "email" | "whatsapp",
  ) => void;
  onUnreachable: (recall: RecallRead) => void;
  onCancel: (recall: RecallRead) => void;
}) {
  const t = useTranslations("recalls");
  return (
    <div className="flex flex-wrap gap-1">
      <Button
        type="button"
        size="sm"
        variant="secondary"
        disabled={disabled}
        onClick={() => onContact(recall, "call")}
        {...testIdProps(recallActionTestId("call", recall.publicId))}
      >
        {t("actions.call")}
      </Button>
      <Button
        type="button"
        size="sm"
        variant="secondary"
        disabled={disabled}
        onClick={() => onContact(recall, "sms")}
        {...testIdProps(recallActionTestId("sms", recall.publicId))}
      >
        {t("actions.sms")}
      </Button>
      <Button
        type="button"
        size="sm"
        variant="secondary"
        disabled={disabled}
        onClick={() => onContact(recall, "email")}
        {...testIdProps(recallActionTestId("email", recall.publicId))}
      >
        {t("actions.email")}
      </Button>
      <Button
        type="button"
        size="sm"
        variant="secondary"
        disabled={disabled}
        onClick={() => onContact(recall, "whatsapp")}
        {...testIdProps(recallActionTestId("whatsapp", recall.publicId))}
      >
        {t("actions.whatsapp")}
      </Button>
      <Button
        type="button"
        size="sm"
        disabled={disabled}
        onClick={() => onBook(recall)}
        {...testIdProps(recallActionTestId("book", recall.publicId))}
      >
        {t("actions.book")}
      </Button>
      <Button
        type="button"
        size="sm"
        variant="ghost"
        disabled={disabled}
        onClick={() => onUnreachable(recall)}
        {...testIdProps(recallActionTestId("unreachable", recall.publicId))}
      >
        {t("actions.unreachable")}
      </Button>
      <Button
        type="button"
        size="sm"
        variant="ghost"
        disabled={disabled}
        onClick={() => onCancel(recall)}
        {...testIdProps(recallActionTestId("cancel", recall.publicId))}
      >
        {t("actions.cancel")}
      </Button>
    </div>
  );
}
