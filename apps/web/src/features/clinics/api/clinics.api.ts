import { apiFetch } from "@/lib/api/client";
import type {
  ClinicalSettingsPut,
  ClinicalSettingsRead,
  ClinicRead,
  ClinicUpdate,
  PageSchemaSiteRead,
  SiteCreate,
  SiteRead,
  SiteUpdate,
} from "@/lib/api/generated";

export async function fetchCurrentClinic(
  locale: string,
  clinicPublicId: string,
): Promise<ClinicRead> {
  return apiFetch<ClinicRead>("/api/v1/clinic", {
    locale,
    clinicPublicId,
  });
}

export async function updateCurrentClinic(
  body: ClinicUpdate,
  locale: string,
  clinicPublicId: string,
): Promise<ClinicRead> {
  return apiFetch<ClinicRead>("/api/v1/clinic", {
    method: "PATCH",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}

export async function fetchSites(
  locale: string,
  clinicPublicId: string,
  params: { limit?: number; offset?: number } = {},
): Promise<PageSchemaSiteRead> {
  const search = new URLSearchParams();
  if (params.limit !== undefined) {
    search.set("limit", String(params.limit));
  }
  if (params.offset !== undefined) {
    search.set("offset", String(params.offset));
  }
  const query = search.toString();
  return apiFetch<PageSchemaSiteRead>(
    `/api/v1/sites${query ? `?${query}` : ""}`,
    { locale, clinicPublicId },
  );
}

export async function createSite(
  body: SiteCreate,
  locale: string,
  clinicPublicId: string,
): Promise<SiteRead> {
  return apiFetch<SiteRead>("/api/v1/sites", {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}

export async function updateSite(
  siteId: string,
  body: SiteUpdate,
  locale: string,
  clinicPublicId: string,
): Promise<SiteRead> {
  return apiFetch<SiteRead>(`/api/v1/sites/${siteId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}

export async function deleteSite(
  siteId: string,
  locale: string,
  clinicPublicId: string,
): Promise<void> {
  await apiFetch<void>(`/api/v1/sites/${siteId}`, {
    method: "DELETE",
    locale,
    clinicPublicId,
  });
}

export async function fetchClinicalSettings(
  locale: string,
  clinicPublicId: string,
): Promise<ClinicalSettingsRead> {
  return apiFetch<ClinicalSettingsRead>("/api/v1/settings/clinical", {
    locale,
    clinicPublicId,
  });
}

export async function updateClinicalSettings(
  body: ClinicalSettingsPut,
  locale: string,
  clinicPublicId: string,
): Promise<ClinicalSettingsRead> {
  return apiFetch<ClinicalSettingsRead>("/api/v1/settings/clinical", {
    method: "PUT",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}
