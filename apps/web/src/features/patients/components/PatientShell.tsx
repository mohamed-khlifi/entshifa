"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { PatientHeaderCard } from "../components/PatientHeaderCard";
import { PatientSafetyAlertBanner } from "../components/PatientSafetyAlertBanner";
import { usePatientQuery } from "../hooks/use-patient-queries";
import { Link, usePathname } from "@/lib/i18n/navigation";
import { Permission } from "@/lib/permissions";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";
import { usePermission } from "@/providers/permission-provider";

export function PatientShell({
  patientId,
  children,
}: {
  patientId: string;
  children: ReactNode;
}) {
  const t = useTranslations("patients");
  const pathname = usePathname();
  const canReadAttachments = usePermission(Permission.ATTACHMENT_READ);
  const patient = usePatientQuery(patientId);
  const overviewHref = `/patients/${patientId}`;
  const attachmentsHref = `/patients/${patientId}/attachments`;

  if (patient.isLoading) {
    return (
      <p
        className="text-sm text-muted-foreground"
        {...testIdProps(testIds.patients.loading)}
      >
        {t("state.loading")}
      </p>
    );
  }

  if (patient.isError || !patient.data) {
    return (
      <p
        className="text-sm text-destructive"
        {...testIdProps(testIds.patients.error)}
      >
        {t("state.loadError")}
      </p>
    );
  }

  return (
    <div className="space-y-6" {...testIdProps(testIds.patients.shell)}>
      <PatientSafetyAlertBanner flags={patient.data.flags} />
      <PatientHeaderCard patient={patient.data} />
      <nav
        className="flex flex-wrap gap-2"
        {...testIdProps(testIds.patients.chartNav)}
      >
        <Link
          href={overviewHref}
          className={cn(
            "rounded-full px-3 py-1.5 text-sm font-medium",
            pathname === overviewHref
              ? "bg-primary/10 text-primary"
              : "text-muted-foreground hover:bg-muted",
          )}
          {...testIdProps(testIds.patients.navOverview)}
        >
          {t("nav.overview")}
        </Link>
        {canReadAttachments ? (
          <Link
            href={attachmentsHref}
            className={cn(
              "rounded-full px-3 py-1.5 text-sm font-medium",
              pathname === attachmentsHref
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted",
            )}
            {...testIdProps(testIds.patients.navAttachments)}
          >
            {t("nav.attachments")}
          </Link>
        ) : null}
      </nav>
      {children}
    </div>
  );
}
