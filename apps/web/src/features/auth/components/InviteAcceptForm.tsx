"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";

import { acceptInvitation } from "@/features/auth/api/auth.api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link } from "@/lib/i18n/navigation";
import { ApiError, resolveErrorMessage } from "@/lib/api/errors";
import { testIdProps, testIds } from "@/lib/test/test-id";

type Props = { token: string };

export function InviteAcceptForm({ token }: Props) {
  const t = useTranslations("auth");
  const tErrors = useTranslations("errors");
  const locale = useLocale();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nameError, setNameError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (firstName.trim().length === 0) {
      setNameError(t("validation.firstNameRequired"));
      return;
    }
    if (lastName.trim().length === 0) {
      setNameError(t("validation.lastNameRequired"));
      return;
    }
    setNameError(null);
    setBusy(true);
    try {
      await acceptInvitation({ token, firstName, lastName, password }, locale);
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
        <p className="text-sm text-muted-foreground">{t("invite.success")}</p>
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
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="invite-first">{t("invite.firstName")}</Label>
          <Input
            id="invite-first"
            autoComplete="given-name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            disabled={busy}
            {...testIdProps(testIds.auth.invite.firstName)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="invite-last">{t("invite.lastName")}</Label>
          <Input
            id="invite-last"
            autoComplete="family-name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            disabled={busy}
            {...testIdProps(testIds.auth.invite.lastName)}
          />
        </div>
      </div>
      {nameError ? (
        <p className="text-sm text-destructive" role="alert">
          {nameError}
        </p>
      ) : null}
      <div className="space-y-2">
        <Label htmlFor="invite-password">{t("invite.password")}</Label>
        <Input
          id="invite-password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={busy}
          {...testIdProps(testIds.auth.invite.password)}
        />
      </div>
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
      <Button
        type="submit"
        className="w-full"
        disabled={busy}
        {...testIdProps(testIds.auth.invite.submit)}
      >
        {t("invite.submit")}
      </Button>
    </form>
  );
}
