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
export type PageSchemaAttachmentRead = Schemas["PageSchema_AttachmentRead_"];
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
export type CodeableConcept = Schemas["CodeableConcept"];
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

export type ConceptAdminRead = Schemas["ConceptAdminRead"];
export type ConceptCreate = Schemas["ConceptCreate"];
export type ConceptUpdate = Schemas["ConceptUpdate"];
export type ConceptTranslationUpsert = Schemas["ConceptTranslationUpsert"];
export type PageSchemaConceptAdminRead =
  Schemas["PageSchema_ConceptAdminRead_"];
export type TranslationCoverageItem = Schemas["TranslationCoverageItem"];
export type PageSchemaTranslationCoverageItem =
  Schemas["PageSchema_TranslationCoverageItem_"];
export type ValueSetMemberCreate = Schemas["ValueSetMemberCreate"];
export type ValueSetSummaryRead = Schemas["ValueSetSummaryRead"];

export type PatientRead = Schemas["PatientRead"];
export type PatientCreate = Schemas["PatientCreate"];
export type PatientUpdate = Schemas["PatientUpdate"];
export type PatientSummaryRead = Schemas["PatientSummaryRead"];
export type PageSchemaPatientSummaryRead =
  Schemas["PageSchema_PatientSummaryRead_"];
export type PatientIdentifierCreate = Schemas["PatientIdentifierCreate"];
export type PatientIdentifierRead = Schemas["PatientIdentifierRead"];
export type PatientAllergyCreate = Schemas["PatientAllergyCreate"];
export type PatientAllergyRead = Schemas["PatientAllergyRead"];
export type PatientMedicationCreate = Schemas["PatientMedicationCreate"];
export type PatientMedicationRead = Schemas["PatientMedicationRead"];
export type PatientFlagCreate = Schemas["PatientFlagCreate"];
export type PatientFlagUpdate = Schemas["PatientFlagUpdate"];
export type PatientFlagRead = Schemas["PatientFlagRead"];
export type PatientProblemCreate = Schemas["PatientProblemCreate"];
export type PatientProblemRead = Schemas["PatientProblemRead"];
export type PatientHistoryCreate = Schemas["PatientHistoryCreate"];
export type PatientHistoryRead = Schemas["PatientHistoryRead"];

export type AppointmentTypeRead = Schemas["AppointmentTypeRead"];
export type AppointmentTypeCreate = Schemas["AppointmentTypeCreate"];
export type AppointmentTypeUpdate = Schemas["AppointmentTypeUpdate"];
export type PageSchemaAppointmentTypeRead =
  Schemas["PageSchema_AppointmentTypeRead_"];
export type AppointmentRead = Schemas["AppointmentRead"];
export type AppointmentCreate = Schemas["AppointmentCreate"];
export type AppointmentUpdate = Schemas["AppointmentUpdate"];
export type PageSchemaAppointmentRead = Schemas["PageSchema_AppointmentRead_"];
export type WaitingRoomEntryRead = Schemas["WaitingRoomEntryRead"];
export type PageSchemaWaitingRoomEntryRead =
  Schemas["PageSchema_WaitingRoomEntryRead_"];
export type SchedulableDoctorRead = Schemas["SchedulableDoctorRead"];
export type PageSchemaSchedulableDoctorRead =
  Schemas["PageSchema_SchedulableDoctorRead_"];

export type DocumentCreate = Schemas["DocumentCreate"];
export type DocumentFinalize = Schemas["DocumentFinalize"];
export type DocumentRead = Schemas["DocumentRead"];
export type DocumentDownloadRead = Schemas["DocumentDownloadRead"];
export type DocumentPreviewRead = Schemas["DocumentPreviewRead"];
export type PageSchemaDocumentRead = Schemas["PageSchema_DocumentRead_"];
export type DocumentTemplateCreate = Schemas["DocumentTemplateCreate"];
export type DocumentTemplateRead = Schemas["DocumentTemplateRead"];
export type DocumentTemplateDetailRead = Schemas["DocumentTemplateDetailRead"];
export type DocumentTemplatePreview = Schemas["DocumentTemplatePreview"];
export type DocumentTemplateVersionCreate =
  Schemas["DocumentTemplateVersionCreate"];
export type DocumentTemplateVersionRead =
  Schemas["DocumentTemplateVersionRead"];
export type PageSchemaDocumentTemplateRead =
  Schemas["PageSchema_DocumentTemplateRead_"];
export type PlaceholderSpec = Schemas["PlaceholderSpec"];

export type NarrativeFindingIn = Schemas["NarrativeFindingIn"];
export type NarrativeRenderRequest = Schemas["NarrativeRenderRequest"];
export type NarrativeRenderRead = Schemas["NarrativeRenderRead"];
export type ObservationCreate = Schemas["ObservationCreate"];
export type ObservationBatchCreate = Schemas["ObservationBatchCreate"];
export type ObservationRead = Schemas["ObservationRead"];
export type PageSchemaObservationRead = Schemas["PageSchema_ObservationRead_"];
export type ExaminationSnapshotCreate = Schemas["ExaminationSnapshotCreate"];
export type ExaminationSnapshotRead = Schemas["ExaminationSnapshotRead"];
export type PageSchemaExaminationSnapshotRead =
  Schemas["PageSchema_ExaminationSnapshotRead_"];
export type EncounterComplaintWrite = Schemas["EncounterComplaintWrite"];
export type EncounterCopyForward = Schemas["EncounterCopyForward"];
export type EncounterCreate = Schemas["EncounterCreate"];
export type EncounterPatch = Schemas["EncounterPatch"];
export type EncounterRead = Schemas["EncounterRead"];
export type EncounterSign = Schemas["EncounterSign"];
export type EncounterAddendumCreate = Schemas["EncounterAddendumCreate"];
export type EncounterTemplateRead = Schemas["EncounterTemplateRead"];
export type EncounterTemplateRouteRequest =
  Schemas["EncounterTemplateRouteRequest"];
export type PageSchemaEncounterRead = Schemas["PageSchema_EncounterRead_"];
export type PageSchemaPatientProblemRead =
  Schemas["PageSchema_PatientProblemRead_"];
