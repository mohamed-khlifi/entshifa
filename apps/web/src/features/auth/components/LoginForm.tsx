"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link, useRouter } from "@/lib/i18n/navigation";
import { ApiError, resolveErrorMessage } from "@/lib/api/errors";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

import {
  createLoginSchema,
  type LoginFormValues,
} from "../schemas/login.schema";

export function LoginForm() {
  const t = useTranslations("auth");
  const tErrors = useTranslations("errors");
  const router = useRouter();
  const { login, completeMfa } = useSession();
  const [apiError, setApiError] = useState<string | null>(null);
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [mfaCode, setMfaCode] = useState("");

  const schema = createLoginSchema(t);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setApiError(null);
    try {
      const result = await login(values.email, values.password);
      if (result.status === "mfa_required") {
        setMfaToken(result.mfaToken);
        return;
      }
      router.replace("/home");
    } catch (error) {
      setApiError(resolveLoginError(error, tErrors));
    }
  });

  const onMfaSubmit = async () => {
    if (!mfaToken) {
      return;
    }
    setApiError(null);
    try {
      await completeMfa(mfaToken, mfaCode);
      router.replace("/home");
    } catch (error) {
      setApiError(resolveLoginError(error, tErrors));
    }
  };

  if (mfaToken) {
    return (
      <div className="space-y-5">
        <p className="text-sm text-muted-foreground">{t("mfa.loginPrompt")}</p>
        <div className="space-y-2">
          <Label htmlFor="mfa-code">{t("mfa.code")}</Label>
          <Input
            id="mfa-code"
            inputMode="numeric"
            autoComplete="one-time-code"
            value={mfaCode}
            onChange={(event) => setMfaCode(event.target.value)}
            {...testIdProps(testIds.auth.mfa.code)}
          />
        </div>
        {apiError ? (
          <p
            className="text-sm text-destructive"
            role="alert"
            {...testIdProps(testIds.auth.login.error)}
          >
            {apiError}
          </p>
        ) : null}
        <Button
          type="button"
          className="w-full"
          onClick={() => void onMfaSubmit()}
          {...testIdProps(testIds.auth.mfa.submit)}
        >
          {t("mfa.verify")}
        </Button>
      </div>
    );
  }

  return (
    <form className="space-y-5" onSubmit={onSubmit} noValidate>
      <div className="space-y-2">
        <Label htmlFor="login-email">{t("login.email")}</Label>
        <Input
          id="login-email"
          type="email"
          autoComplete="username"
          disabled={isSubmitting}
          {...testIdProps(testIds.auth.login.email)}
          {...register("email")}
        />
        {errors.email ? (
          <p className="text-sm text-destructive" role="alert">
            {errors.email.message}
          </p>
        ) : null}
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2">
          <Label htmlFor="login-password">{t("login.password")}</Label>
          <Link
            href="/password-reset"
            className="text-xs font-medium text-primary hover:underline"
            {...testIdProps(testIds.auth.passwordReset.link)}
          >
            {t("login.forgotPassword")}
          </Link>
        </div>
        <Input
          id="login-password"
          type="password"
          autoComplete="current-password"
          disabled={isSubmitting}
          {...testIdProps(testIds.auth.login.password)}
          {...register("password")}
        />
        {errors.password ? (
          <p className="text-sm text-destructive" role="alert">
            {errors.password.message}
          </p>
        ) : null}
      </div>
      {apiError ? (
        <p
          className="text-sm text-destructive"
          role="alert"
          {...testIdProps(testIds.auth.login.error)}
        >
          {apiError}
        </p>
      ) : null}
      <Button
        type="submit"
        className="w-full"
        disabled={isSubmitting}
        {...testIdProps(testIds.auth.login.submit)}
      >
        {t("login.submit")}
      </Button>
    </form>
  );
}

function resolveLoginError(
  error: unknown,
  tErrors: ReturnType<typeof useTranslations<"errors">>,
): string {
  if (error instanceof ApiError) {
    return resolveErrorMessage(
      error,
      (key) => tErrors(key as Parameters<typeof tErrors>[0]),
      (key) => tErrors.has(key as Parameters<typeof tErrors.has>[0]),
    );
  }
  return tErrors("generic");
}
