"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useRouter } from "@/lib/i18n/navigation";
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
  const { login } = useSession();
  const [apiError, setApiError] = useState<string | null>(null);

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
      await login(values.email, values.password);
      router.replace("/home");
    } catch (error) {
      if (error instanceof ApiError) {
        setApiError(
          resolveErrorMessage(
            error,
            (key) => tErrors(key as Parameters<typeof tErrors>[0]),
            (key) => tErrors.has(key as Parameters<typeof tErrors.has>[0]),
          ),
        );
        return;
      }
      setApiError(tErrors("generic"));
    }
  });

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
        <Label htmlFor="login-password">{t("login.password")}</Label>
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
        <div
          className="rounded-lg border border-destructive/25 bg-destructive/5 px-3 py-2 text-sm text-destructive"
          role="alert"
          {...testIdProps(testIds.auth.login.error)}
        >
          {apiError}
        </div>
      ) : null}
      <Button
        type="submit"
        className="h-11 w-full shadow-sm"
        disabled={isSubmitting}
        {...testIdProps(testIds.auth.login.submit)}
      >
        {t("login.submit")}
      </Button>
    </form>
  );
}
