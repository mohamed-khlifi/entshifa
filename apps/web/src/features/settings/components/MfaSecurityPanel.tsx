"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import QRCode from "qrcode";

import { confirmMfa, disableMfa, enrollMfa, useMeQuery } from "@/features/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ApiError, resolveErrorMessage } from "@/lib/api/errors";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";
import { queryKeys } from "@/lib/api/query-keys";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export function MfaSecurityPanel() {
  const t = useTranslations("settings");
  const tErrors = useTranslations("errors");
  const locale = useLocale();
  const { session } = useSession();
  const queryClient = useQueryClient();
  const { data: me } = useMeQuery();
  const mfaEnabled = me?.mfaEnabled ?? false;
  const [enroll, setEnroll] = useState<{
    secret: string;
    provisioningUri: string;
  } | null>(null);
  const [confirmCode, setConfirmCode] = useState("");
  const [disablePassword, setDisablePassword] = useState("");
  const [disableCode, setDisableCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const invalidateMe = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.auth.me() });
  };

  const resolveErr = (err: unknown) =>
    err instanceof ApiError
      ? resolveErrorMessage(
          err,
          (key) => tErrors(key as Parameters<typeof tErrors>[0]),
          (key) => tErrors.has(key as Parameters<typeof tErrors.has>[0]),
        )
      : tErrors("generic");

  const startEnroll = async () => {
    if (!session) return;
    setError(null);
    setBusy(true);
    try {
      const res = await enrollMfa(locale, session.clinicPublicId);
      setEnroll({
        secret: res.secret,
        provisioningUri: res.provisioningUri,
      });
    } catch (err) {
      setError(resolveErr(err));
    } finally {
      setBusy(false);
    }
  };

  const submitConfirm = async () => {
    if (!session) return;
    setError(null);
    setBusy(true);
    try {
      await confirmMfa({ code: confirmCode }, locale, session.clinicPublicId);
      setEnroll(null);
      setConfirmCode("");
      await invalidateMe();
      toast.success(t("security.enrollSuccess"));
    } catch (err) {
      setError(resolveErr(err));
    } finally {
      setBusy(false);
    }
  };

  const submitDisable = async () => {
    if (!session) return;
    setError(null);
    setBusy(true);
    try {
      await disableMfa(
        { password: disablePassword, code: disableCode },
        locale,
        session.clinicPublicId,
      );
      setDisablePassword("");
      setDisableCode("");
      await invalidateMe();
      toast.success(t("security.disableSuccess"));
    } catch (err) {
      setError(resolveErr(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card
      className="border-border/80 shadow-sm"
      {...testIdProps(testIds.settings.securityRoot)}
    >
      <CardHeader>
        <CardTitle>{t("security.mfaTitle")}</CardTitle>
        <CardDescription>{t("security.mfaDescription")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-sm text-muted-foreground">
          {mfaEnabled ? t("security.mfaEnabled") : t("security.mfaDisabled")}
        </p>
        {error ? (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        ) : null}

        {!mfaEnabled && !enroll ? (
          <Button
            type="button"
            onClick={() => void startEnroll()}
            disabled={busy}
            {...testIdProps(testIds.settings.mfaEnroll)}
          >
            {t("security.enroll")}
          </Button>
        ) : null}

        {enroll ? (
          <div className="space-y-4 rounded-lg border border-border bg-muted/30 p-4">
            <p className="text-sm">{t("security.scanQr")}</p>
            <AuthenticatorQr value={enroll.provisioningUri} />
            <div className="space-y-2">
              <Label>{t("security.secretLabel")}</Label>
              <p className="font-mono text-sm">{enroll.secret}</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="mfa-confirm">{t("security.confirmCode")}</Label>
              <Input
                id="mfa-confirm"
                inputMode="numeric"
                value={confirmCode}
                onChange={(e) => setConfirmCode(e.target.value)}
                {...testIdProps(testIds.settings.mfaConfirmCode)}
              />
            </div>
            <Button
              type="button"
              onClick={() => void submitConfirm()}
              disabled={busy}
              {...testIdProps(testIds.settings.mfaConfirmSubmit)}
            >
              {t("security.confirmSubmit")}
            </Button>
          </div>
        ) : null}

        {mfaEnabled ? (
          <div className="space-y-4 rounded-lg border border-border p-4">
            <p className="text-sm font-medium">{t("security.disableTitle")}</p>
            <div className="space-y-2">
              <Label htmlFor="mfa-disable-pw">
                {t("security.disablePassword")}
              </Label>
              <Input
                id="mfa-disable-pw"
                type="password"
                value={disablePassword}
                onChange={(e) => setDisablePassword(e.target.value)}
                {...testIdProps(testIds.settings.mfaDisablePassword)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="mfa-disable-code">
                {t("security.disableCode")}
              </Label>
              <Input
                id="mfa-disable-code"
                inputMode="numeric"
                value={disableCode}
                onChange={(e) => setDisableCode(e.target.value)}
                {...testIdProps(testIds.settings.mfaDisableCode)}
              />
            </div>
            <Button
              type="button"
              variant="secondary"
              onClick={() => void submitDisable()}
              disabled={busy}
              {...testIdProps(testIds.settings.mfaDisableSubmit)}
            >
              {t("security.disableSubmit")}
            </Button>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function AuthenticatorQr({ value }: { value: string }) {
  const t = useTranslations("settings");
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    setSrc(null);
    setFailed(false);
    void QRCode.toDataURL(value, {
      margin: 1,
      width: 220,
      errorCorrectionLevel: "M",
      color: { dark: "#111827", light: "#ffffff" },
    })
      .then((url) => {
        if (active) {
          setSrc(url);
        }
      })
      .catch(() => {
        if (active) {
          setFailed(true);
        }
      });
    return () => {
      active = false;
    };
  }, [value]);

  if (failed) {
    return (
      <p className="break-all font-mono text-xs text-muted-foreground">
        {value}
      </p>
    );
  }

  return (
    <div className="flex justify-center">
      <div className="rounded-2xl border border-border bg-white p-3 shadow-sm">
        {src ? (
          // Drawn in the browser from the setup link. The secret is not sent out.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={src}
            width={220}
            height={220}
            alt={t("security.qrAlt")}
            className="h-[220px] w-[220px]"
            {...testIdProps(testIds.settings.mfaQr)}
          />
        ) : (
          <div className="h-[220px] w-[220px] animate-pulse rounded-lg bg-muted" />
        )}
      </div>
    </div>
  );
}
