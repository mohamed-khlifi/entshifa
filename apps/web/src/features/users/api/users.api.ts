import { apiFetch } from "@/lib/api/client";
import type {
  CustomRoleCreate,
  CustomRoleUpdate,
  InvitationCreate,
  InvitationRead,
  PageSchemaUserRead,
  PermissionRead,
  RoleAssignment,
  RoleRead,
  UserRead,
  UserUpdate,
} from "@/lib/api/generated";

export async function fetchUsers(
  locale: string,
  clinicPublicId: string,
  params: { limit?: number; offset?: number; search?: string } = {},
): Promise<PageSchemaUserRead> {
  const search = new URLSearchParams();
  if (params.limit !== undefined) {
    search.set("limit", String(params.limit));
  }
  if (params.offset !== undefined) {
    search.set("offset", String(params.offset));
  }
  if (params.search) {
    search.set("search", params.search);
  }
  const query = search.toString();
  return apiFetch<PageSchemaUserRead>(
    `/api/v1/users${query ? `?${query}` : ""}`,
    { locale, clinicPublicId },
  );
}

export async function updateUser(
  userId: string,
  body: UserUpdate,
  locale: string,
  clinicPublicId: string,
): Promise<UserRead> {
  return apiFetch<UserRead>(`/api/v1/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}

export async function fetchRoles(
  locale: string,
  clinicPublicId: string,
): Promise<RoleRead[]> {
  return apiFetch<RoleRead[]>("/api/v1/roles", {
    locale,
    clinicPublicId,
  });
}

export async function fetchPermissions(
  locale: string,
  clinicPublicId: string,
): Promise<PermissionRead[]> {
  return apiFetch<PermissionRead[]>("/api/v1/permissions", {
    locale,
    clinicPublicId,
  });
}

export async function createRole(
  body: CustomRoleCreate,
  locale: string,
  clinicPublicId: string,
): Promise<RoleRead> {
  return apiFetch<RoleRead>("/api/v1/roles", {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}

export async function updateRole(
  roleId: string,
  body: CustomRoleUpdate,
  locale: string,
  clinicPublicId: string,
): Promise<RoleRead> {
  return apiFetch<RoleRead>(`/api/v1/roles/${roleId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}

export async function createInvitation(
  body: InvitationCreate,
  locale: string,
  clinicPublicId: string,
): Promise<InvitationRead> {
  return apiFetch<InvitationRead>("/api/v1/invitations", {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}

export async function assignUserRole(
  userId: string,
  body: RoleAssignment,
  locale: string,
  clinicPublicId: string,
): Promise<UserRead> {
  return apiFetch<UserRead>(`/api/v1/users/${userId}/roles`, {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}
