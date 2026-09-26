"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

import { requestPasswordReset } from "@/features/auth/api/auth.api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link } from "@/lib/i18n/navigation";
import { ApiError, resolveErrorMessage } from "@/lib/api/errors";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { useLocale } from "next-intl";

export function PasswordResetRequestForm() {
  const t = useTranslations("auth");
  const tErrors = useTranslations("errors");
  const locale = useLocale();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await requestPasswordReset({ email }, locale);
      setSent(true);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? resolveErrorMessage(
              err,
              (key) => tErrors(key as Parameters<typeof tErrors>[0]),
              (key) => tErrors.has(key as Parameters<typeof tErrors.has>[0]),
            )
          : tErrors("generic"),
      );
    } finally {
      setBusy(false);
    }
  };

  if (sent) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">{t("passwordReset.sent")}</p>
        <Link
          href="/login"
          className="text-sm font-medium text-primary hover:underline"
        >
          {t("passwordReset.backToLogin")}
        </Link>
      </div>
    );
  }

  return (
    <form className="space-y-5" onSubmit={onSubmit} noValidate>
      <div className="space-y-2">
        <Label htmlFor="reset-email">{t("passwordReset.email")}</Label>
        <Input
          id="reset-email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={busy}
          {...testIdProps(testIds.auth.passwordReset.email)}
        />
      </div>
      {error ? (
        <p className="text-sm text-destructive" role="alert">{error}</p>
      ) : null}
      <Button
        type="submit"
        className="w-full"
        disabled={busy}
        {...testIdProps(testIds.auth.passwordReset.submit)}
      >
        {t("passwordReset.submit")}
      </Button>
      <Link
        href="/login"
        className="block text-center text-sm text-muted-foreground hover:text-foreground"
      >
        {t("passwordReset.backToLogin")}
      </Link>
    </form>
  );
}
