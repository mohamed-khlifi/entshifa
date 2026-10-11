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
  const canFinalizeDocuments = usePermission(Permission.DOCUMENT_FINALIZE);
  const canPrescribe = usePermission(Permission.PRESCRIPTION_CREATE);
  const patient = usePatientQuery(patientId);
  const overviewHref = `/patients/${patientId}`;
  const attachmentsHref = `/patients/${patientId}/attachments`;
  const documentsHref = `/patients/${patientId}/documents`;
  const examinationHref = `/patients/${patientId}/examination`;
  const prescriptionsHref = `/patients/${patientId}/prescriptions`;

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
        <Link
          href={`/patients/${patientId}/consultation`}
          className={cn(
            "rounded-full px-3 py-1.5 text-sm font-medium",
            pathname === `/patients/${patientId}/consultation` ||
              pathname.startsWith(`/patients/${patientId}/encounters/`)
              ? "bg-primary/10 text-primary"
              : "text-muted-foreground hover:bg-muted",
          )}
          {...testIdProps(testIds.patients.navConsultation)}
        >
          {t("nav.consultation")}
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
        <Link
          href={examinationHref}
          className={cn(
            "rounded-full px-3 py-1.5 text-sm font-medium",
            pathname === examinationHref
              ? "bg-primary/10 text-primary"
              : "text-muted-foreground hover:bg-muted",
          )}
          {...testIdProps(testIds.patients.navExamination)}
        >
          {t("nav.examination")}
        </Link>
        {canPrescribe ? (
          <Link
            href={prescriptionsHref}
            className={cn(
              "rounded-full px-3 py-1.5 text-sm font-medium",
              pathname === prescriptionsHref
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted",
            )}
            {...testIdProps(testIds.patients.navPrescriptions)}
          >
            {t("nav.prescriptions")}
          </Link>
        ) : null}
        <Link
          href={`/patients/${patientId}/timeline`}
          className={cn(
            "rounded-full px-3 py-1.5 text-sm font-medium",
            pathname === `/patients/${patientId}/timeline`
              ? "bg-primary/10 text-primary"
              : "text-muted-foreground hover:bg-muted",
          )}
          {...testIdProps(testIds.patients.navTimeline)}
        >
          {t("nav.timeline")}
        </Link>
        {canFinalizeDocuments ? (
          <Link
            href={documentsHref}
            className={cn(
              "rounded-full px-3 py-1.5 text-sm font-medium",
              pathname === documentsHref
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted",
            )}
            {...testIdProps(testIds.documents.patientNav)}
          >
            {t("nav.documents")}
          </Link>
        ) : null}
      </nav>
      {children}
    </div>
  );
}
