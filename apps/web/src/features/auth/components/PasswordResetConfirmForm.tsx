"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";

import { confirmPasswordReset } from "@/features/auth/api/auth.api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link } from "@/lib/i18n/navigation";
import { ApiError, resolveErrorMessage } from "@/lib/api/errors";
import { testIdProps, testIds } from "@/lib/test/test-id";

type Props = { token: string };

export function PasswordResetConfirmForm({ token }: Props) {
  const t = useTranslations("auth");
  const tErrors = useTranslations("errors");
  const locale = useLocale();
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await confirmPasswordReset({ token, password }, locale);
      setDone(true);
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

  if (done) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          {t("passwordReset.confirmSuccess")}
        </p>
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
        <Label htmlFor="reset-password">{t("passwordReset.password")}</Label>
        <Input
          id="reset-password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={busy}
          {...testIdProps(testIds.auth.passwordReset.password)}
        />
      </div>
      {error ? (
        <p className="text-sm text-destructive" role="alert">{error}</p>
      ) : null}
      <Button
        type="submit"
        className="w-full"
        disabled={busy}
        {...testIdProps(testIds.auth.passwordReset.confirmSubmit)}
      >
        {t("passwordReset.confirmSubmit")}
      </Button>
    </form>
  );
}
