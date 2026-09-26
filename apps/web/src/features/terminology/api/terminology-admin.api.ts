import { apiFetch } from "@/lib/api/client";
import type {
  ConceptAdminRead,
  ConceptCreate,
  ConceptTranslationUpsert,
  ConceptUpdate,
  PageSchemaConceptAdminRead,
  PageSchemaTranslationCoverageItem,
  ValueSetMemberCreate,
  ValueSetRead,
  ValueSetSummaryRead,
} from "@/lib/api/generated";

export async function fetchAdminConcepts(
  locale: string,
  clinicPublicId: string,
  params: {
    q?: string;
    kind?: string;
    limit?: number;
    offset?: number;
    clinicOwnedOnly?: boolean;
  } = {},
): Promise<PageSchemaConceptAdminRead> {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.kind) search.set("kind", params.kind);
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  if (params.clinicOwnedOnly) search.set("clinicOwnedOnly", "true");
  const query = search.toString();
  return apiFetch<PageSchemaConceptAdminRead>(
    `/api/v1/terminology/admin/concepts${query ? `?${query}` : ""}`,
    { locale, clinicPublicId },
  );
}

export async function createClinicConcept(
  body: ConceptCreate,
  locale: string,
  clinicPublicId: string,
): Promise<ConceptAdminRead> {
  return apiFetch<ConceptAdminRead>("/api/v1/terminology/admin/concepts", {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}

export async function updateClinicConcept(
  publicId: string,
  body: ConceptUpdate,
  locale: string,
  clinicPublicId: string,
): Promise<ConceptAdminRead> {
  return apiFetch<ConceptAdminRead>(
    `/api/v1/terminology/admin/concepts/${publicId}`,
    {
      method: "PATCH",
      body: JSON.stringify(body),
      locale,
      clinicPublicId,
    },
  );
}

export async function upsertClinicTranslation(
  publicId: string,
  translationLocale: string,
  body: ConceptTranslationUpsert,
  locale: string,
  clinicPublicId: string,
): Promise<ConceptAdminRead> {
  return apiFetch<ConceptAdminRead>(
    `/api/v1/terminology/admin/concepts/${publicId}/translations/${translationLocale}`,
    {
      method: "PUT",
      body: JSON.stringify(body),
      locale,
      clinicPublicId,
    },
  );
}

export async function fetchValueSets(
  locale: string,
  clinicPublicId: string,
): Promise<ValueSetSummaryRead[]> {
  return apiFetch<ValueSetSummaryRead[]>(
    "/api/v1/terminology/admin/value-sets",
    {
      locale,
      clinicPublicId,
    },
  );
}

export async function fetchValueSet(
  code: string,
  locale: string,
  clinicPublicId: string,
): Promise<ValueSetRead> {
  return apiFetch<ValueSetRead>(
    `/api/v1/terminology/value-sets/${encodeURIComponent(code)}?locale=${encodeURIComponent(locale)}`,
    { locale, clinicPublicId },
  );
}

export async function addValueSetMember(
  code: string,
  body: ValueSetMemberCreate,
  locale: string,
  clinicPublicId: string,
): Promise<ValueSetRead> {
  return apiFetch<ValueSetRead>(
    `/api/v1/terminology/admin/value-sets/${encodeURIComponent(code)}/members`,
    {
      method: "POST",
      body: JSON.stringify(body),
      locale,
      clinicPublicId,
    },
  );
}

export async function fetchTranslationCoverage(
  targetLocale: string,
  locale: string,
  clinicPublicId: string,
  params: { limit?: number; offset?: number } = {},
): Promise<PageSchemaTranslationCoverageItem> {
  const search = new URLSearchParams({ locale: targetLocale });
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  return apiFetch<PageSchemaTranslationCoverageItem>(
    `/api/v1/terminology/admin/translation-coverage?${search.toString()}`,
    { locale, clinicPublicId },
  );
}
