"use client";

import { useTranslations } from "next-intl";

import { Link, usePathname } from "@/lib/i18n/navigation";
import { Permission } from "@/lib/permissions";
import { cn } from "@/lib/utils/cn";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { usePermission } from "@/providers/permission-provider";

function navClass(active: boolean): string {
  return cn(
    "rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
    active
      ? "bg-primary/10 text-primary"
      : "text-muted-foreground hover:bg-muted hover:text-foreground",
  );
}

export function Sidebar() {
  const t = useTranslations("common");
  const pathname = usePathname();
  const canAdminClinic = usePermission(Permission.ADMIN_CLINIC);
  const canAdminUsers = usePermission(Permission.ADMIN_USERS);
  const canAdminTerminology = usePermission(Permission.ADMIN_TERMINOLOGY);
  const canReadClinicPatients = usePermission(Permission.PATIENT_READ_CLINIC);
  const canReadOwnPatients = usePermission(Permission.PATIENT_READ_OWN);
  const canReadPatients = canReadClinicPatients || canReadOwnPatients;
  const canReadSchedule = usePermission(Permission.APPOINTMENT_READ);

  const homeActive = pathname === "/home" || pathname.startsWith("/home/");
  const clinicActive =
    pathname.startsWith("/admin/clinic") || pathname === "/admin/clinic";
  const usersActive = pathname.startsWith("/admin/users");
  const terminologyActive = pathname.startsWith("/admin/terminology");
  const securityActive = pathname.startsWith("/settings/security");
  const patientsActive = pathname.startsWith("/patients");
  const scheduleActive = pathname.startsWith("/schedule");

  return (
    <aside
      className="hidden h-full w-56 shrink-0 overflow-y-auto border-e border-border bg-card shadow-sm md:block"
      {...testIdProps(testIds.layout.sidebar)}
    >
      <nav className="flex flex-col gap-1 p-4">
        <Link href="/home" className={navClass(homeActive)}>
          {t("nav.home")}
        </Link>
        {canReadPatients ? (
          <Link
            href="/patients"
            className={navClass(patientsActive)}
            {...testIdProps(testIds.patients.nav)}
          >
            {t("nav.patients")}
          </Link>
        ) : null}
        {canReadSchedule ? (
          <Link
            href="/schedule"
            className={navClass(scheduleActive)}
            {...testIdProps(testIds.scheduling.nav)}
          >
            {t("nav.schedule")}
          </Link>
        ) : null}
        <Link href="/settings/security" className={navClass(securityActive)}>
          {t("nav.security")}
        </Link>
        {canAdminClinic || canAdminUsers || canAdminTerminology ? (
          <p className="px-3 pt-4 pb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t("nav.admin")}
          </p>
        ) : null}
        {canAdminClinic ? (
          <Link href="/admin/clinic" className={navClass(clinicActive)}>
            {t("nav.clinic")}
          </Link>
        ) : null}
        {canAdminUsers ? (
          <Link href="/admin/users" className={navClass(usersActive)}>
            {t("nav.users")}
          </Link>
        ) : null}
        {canAdminTerminology ? (
          <Link
            href="/admin/terminology"
            className={navClass(terminologyActive)}
          >
            {t("nav.terminology")}
          </Link>
        ) : null}
      </nav>
    </aside>
  );
}
