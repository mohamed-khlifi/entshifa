/**
 * Generated API wire types.
 *
 * Source of truth: `packages/contracts/openapi.json` via `make contracts`.
 * Prefer these aliases over hand-written request/response types.
 */

export type { components, operations, paths } from "@entshifa/contracts";

import type { components } from "@entshifa/contracts";

type Schemas = components["schemas"];

export type LoginRequest = Schemas["LoginRequest"];
export type LoginResponse = Schemas["LoginResponse"];
export type MeResponse = Schemas["MeResponse"];
export type SessionPayload = Schemas["SessionResponse"];

export type LiveHealthResponse = Schemas["LiveHealthResponse"];
export type ReadyHealthResponse = Schemas["ReadyHealthResponse"];

export type ConceptSearchResponse = Schemas["ConceptSearchResponse"];
export type ConceptDictionaryResponse = Schemas["ConceptDictionaryResponse"];
export type ValueSetRead = Schemas["ValueSetRead"];
export type ResolvedConcept = Schemas["ResolvedConcept"];

export type AttachmentUploadUrlRequest = Schemas["AttachmentUploadUrlRequest"];
export type AttachmentUploadUrlResponse =
  Schemas["AttachmentUploadUrlResponse"];
export type AttachmentConfirmRequest = Schemas["AttachmentConfirmRequest"];
export type AttachmentRead = Schemas["AttachmentRead"];
export type AttachmentDownloadUrlResponse =
  Schemas["AttachmentDownloadUrlResponse"];
export type MediaVariantRead = Schemas["MediaVariantRead"];
export type PresignedUrlResponse = Schemas["PresignedUrlResponse"];

export type ClinicRead = Schemas["ClinicRead"];
export type ClinicUpdate = Schemas["ClinicUpdate"];
export type SiteRead = Schemas["SiteRead"];
export type SiteCreate = Schemas["SiteCreate"];
export type SiteUpdate = Schemas["SiteUpdate"];
export type PageSchemaSiteRead = Schemas["PageSchema_SiteRead_"];
export type ClinicalSettingsRead = Schemas["ClinicalSettingsRead"];
export type ClinicalSettingsPut = Schemas["ClinicalSettingsPut"];
export type ResolvedSettingRead = Schemas["ResolvedSettingRead"];

export type UserRead = Schemas["UserRead"];
export type UserUpdate = Schemas["UserUpdate"];
export type PageSchemaUserRead = Schemas["PageSchema_UserRead_"];
export type RoleRead = Schemas["RoleRead"];
export type PermissionRead = Schemas["PermissionRead"];
export type CustomRoleCreate = Schemas["CustomRoleCreate"];
export type CustomRoleUpdate = Schemas["CustomRoleUpdate"];
export type RoleAssignment = Schemas["RoleAssignment"];
export type InvitationCreate = Schemas["InvitationCreate"];
export type InvitationRead = Schemas["InvitationRead"];
export type InvitationAccept = Schemas["InvitationAccept"];
export type PasswordResetRequest = Schemas["PasswordResetRequest"];
export type PasswordResetConfirm = Schemas["PasswordResetConfirm"];
export type MfaCode = Schemas["MfaCode"];
export type MfaDisable = Schemas["MfaDisable"];
export type MfaLogin = Schemas["MfaLogin"];
export type MfaEnrollResponse = Schemas["MfaEnrollResponse"];
export type ActiveClinicRequest = Schemas["ActiveClinicRequest"];
export type ClinicMembershipList = Schemas["ClinicMembershipList"];
export type ClinicMembershipRead = Schemas["ClinicMembershipRead"];
