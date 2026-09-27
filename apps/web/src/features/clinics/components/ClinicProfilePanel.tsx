"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { CLINIC_DOCUMENT_SETTING_KEYS } from "@/features/clinics/constants";
import {
  useCurrentClinicQuery,
  useUpdateClinicMutation,
} from "@/features/clinics/hooks/use-clinic-queries";
import {
  AttachmentViewer,
  confirmAttachmentUpload,
  requestAttachmentUploadUrl,
} from "@/features/attachments";
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
import { testIdProps, testIds } from "@/lib/test/test-id";
import { useLocale } from "next-intl";
import type { ClinicUpdate } from "@/lib/api/generated";
import { useSession } from "@/providers/session-provider";

function readDocSetting(
  settings: Record<string, unknown>,
  key: string,
): string {
  const value = settings[key];
  return typeof value === "string" ? value : "";
}

export function ClinicProfilePanel() {
  const t = useTranslations("clinics");
  const locale = useLocale();
  const { session } = useSession();
  const { data: clinic, isLoading } = useCurrentClinicQuery();
  const updateClinic = useUpdateClinicMutation();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [city, setCity] = useState("");
  const [documentHeader, setDocumentHeader] = useState("");
  const [documentFooter, setDocumentFooter] = useState("");
  const [signatureId, setSignatureId] = useState("");
  const [logoBusy, setLogoBusy] = useState(false);
  const [signatureBusy, setSignatureBusy] = useState(false);

  useEffect(() => {
    if (!clinic) return;
    setName(clinic.name);
    setEmail(clinic.email ?? "");
    setPhone(clinic.phone ?? "");
    setCity(clinic.city ?? "");
    const settings = clinic.settings as Record<string, unknown>;
    setDocumentHeader(
      readDocSetting(settings, CLINIC_DOCUMENT_SETTING_KEYS.headerHtml),
    );
    setDocumentFooter(
      readDocSetting(settings, CLINIC_DOCUMENT_SETTING_KEYS.footerHtml),
    );
    setSignatureId(
      readDocSetting(
        settings,
        CLINIC_DOCUMENT_SETTING_KEYS.signatureAttachmentPublicId,
      ),
    );
  }, [clinic]);

  const onSaveProfile = () => {
    if (!clinic) return;
    const settings = {
      ...(clinic.settings as Record<string, unknown>),
      [CLINIC_DOCUMENT_SETTING_KEYS.headerHtml]: documentHeader || null,
      [CLINIC_DOCUMENT_SETTING_KEYS.footerHtml]: documentFooter || null,
      [CLINIC_DOCUMENT_SETTING_KEYS.signatureAttachmentPublicId]:
        signatureId || null,
    };
    void updateClinic.mutateAsync({
      name,
      email: email || null,
      phone: phone || null,
      city: city || null,
      settings: settings as unknown as ClinicUpdate["settings"],
    });
  };

  const onLogoChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !session) return;
    setLogoBusy(true);
    try {
      const uploadMeta = await requestAttachmentUploadUrl(
        {
          category: "logo",
          filename: file.name,
          contentType: file.type,
          sizeBytes: file.size,
          isConsentedForTeaching: false,
        },
        locale,
        session.clinicPublicId,
      );
      await fetch(uploadMeta.upload.url, {
        method: uploadMeta.upload.method,
        headers: uploadMeta.upload.headers,
        body: file,
      });
      const attachment = await confirmAttachmentUpload(
        { uploadToken: uploadMeta.uploadToken },
        locale,
        session.clinicPublicId,
      );
      await updateClinic.mutateAsync({
        logoAttachmentPublicId: attachment.publicId,
      });
    } finally {
      setLogoBusy(false);
      event.target.value = "";
    }
  };

  const onSignatureChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file || !session || !clinic) return;
    setSignatureBusy(true);
    try {
      const uploadMeta = await requestAttachmentUploadUrl(
        {
          category: "signature",
          filename: file.name,
          contentType: file.type,
          sizeBytes: file.size,
          isConsentedForTeaching: false,
        },
        locale,
        session.clinicPublicId,
      );
      await fetch(uploadMeta.upload.url, {
        method: uploadMeta.upload.method,
        headers: uploadMeta.upload.headers,
        body: file,
      });
      const attachment = await confirmAttachmentUpload(
        { uploadToken: uploadMeta.uploadToken },
        locale,
        session.clinicPublicId,
      );
      const settings = {
        ...(clinic.settings as Record<string, unknown>),
        [CLINIC_DOCUMENT_SETTING_KEYS.headerHtml]: documentHeader || null,
        [CLINIC_DOCUMENT_SETTING_KEYS.footerHtml]: documentFooter || null,
        [CLINIC_DOCUMENT_SETTING_KEYS.signatureAttachmentPublicId]:
          attachment.publicId,
      };
      await updateClinic.mutateAsync({
        settings: settings as unknown as ClinicUpdate["settings"],
      });
      setSignatureId(attachment.publicId);
    } finally {
      setSignatureBusy(false);
      event.target.value = "";
    }
  };

  if (isLoading || !clinic) {
    return (
      <p className="text-sm text-muted-foreground">
        {t("profile.description")}
      </p>
    );
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <Card
        className="border-border/80 shadow-sm"
        {...testIdProps(testIds.clinics.profileForm)}
      >
        <CardHeader>
          <CardTitle>{t("profile.title")}</CardTitle>
          <CardDescription>{t("profile.description")}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="clinic-name">{t("profile.name")}</Label>
            <Input
              id="clinic-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="clinic-email">{t("profile.email")}</Label>
            <Input
              id="clinic-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="clinic-phone">{t("profile.phone")}</Label>
            <Input
              id="clinic-phone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="clinic-city">{t("profile.city")}</Label>
            <Input
              id="clinic-city"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            />
          </div>
          <div className="sm:col-span-2">
            <Button
              type="button"
              onClick={onSaveProfile}
              disabled={updateClinic.isPending}
              {...testIdProps(testIds.clinics.profileSave)}
            >
              {t("profile.save")}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/80 shadow-sm">
        <CardHeader>
          <CardTitle>{t("branding.title")}</CardTitle>
          <CardDescription>{t("branding.description")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
            {clinic.logoAttachmentPublicId ? (
              <AttachmentViewer
                attachmentPublicId={clinic.logoAttachmentPublicId}
                className="size-24 rounded-lg border border-border object-contain bg-background"
              />
            ) : (
              <div className="flex size-24 items-center justify-center rounded-lg border border-dashed border-border bg-muted/40 text-xs text-muted-foreground">
                {t("branding.logo")}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="clinic-logo">{t("branding.uploadLogo")}</Label>
              <p className="text-xs text-muted-foreground">
                {t("branding.logoHint")}
              </p>
              <Input
                id="clinic-logo"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                disabled={logoBusy}
                onChange={(e) => void onLogoChange(e)}
                {...testIdProps(testIds.clinics.logoInput)}
              />
            </div>
          </div>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
            {signatureId ? (
              <AttachmentViewer
                attachmentPublicId={signatureId}
                className="h-16 w-40 rounded-lg border border-border object-contain bg-background"
              />
            ) : (
              <div className="flex h-16 w-40 items-center justify-center rounded-lg border border-dashed border-border bg-muted/40 text-xs text-muted-foreground">
                {t("branding.signature")}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="clinic-signature">
                {t("branding.uploadSignature")}
              </Label>
              <p className="text-xs text-muted-foreground">
                {t("branding.signatureHint")}
              </p>
              <Input
                id="clinic-signature"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                disabled={signatureBusy}
                onChange={(event) => void onSignatureChange(event)}
                {...testIdProps(testIds.documents.signatureInput)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="doc-header">{t("branding.documentHeader")}</Label>
            <textarea
              id="doc-header"
              className="min-h-[88px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder={t("branding.headerPlaceholder")}
              value={documentHeader}
              onChange={(e) => setDocumentHeader(e.target.value)}
              {...testIdProps(testIds.clinics.documentHeader)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="doc-footer">{t("branding.documentFooter")}</Label>
            <textarea
              id="doc-footer"
              className="min-h-[88px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder={t("branding.footerPlaceholder")}
              value={documentFooter}
              onChange={(e) => setDocumentFooter(e.target.value)}
              {...testIdProps(testIds.clinics.documentFooter)}
            />
          </div>
          <Button
            type="button"
            onClick={onSaveProfile}
            disabled={updateClinic.isPending}
          >
            {t("profile.save")}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
