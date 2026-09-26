/**
 * Generated API wire types.
 *
 * Source of truth: `packages/contracts/openapi.json` via `make contracts`.
 * Prefer these aliases over hand-written request/response types.
 */

export type { components, operations, paths } from '@entshifa/contracts';

import type { components } from '@entshifa/contracts';

type Schemas = components['schemas'];

export type LoginRequest = Schemas['LoginRequest'];
export type LoginResponse = Schemas['LoginResponse'];
export type MeResponse = Schemas['MeResponse'];
export type SessionPayload = Schemas['SessionResponse'];

export type LiveHealthResponse = Schemas['LiveHealthResponse'];
export type ReadyHealthResponse = Schemas['ReadyHealthResponse'];

export type ConceptSearchResponse = Schemas['ConceptSearchResponse'];
export type ConceptDictionaryResponse = Schemas['ConceptDictionaryResponse'];
export type ValueSetRead = Schemas['ValueSetRead'];
export type ResolvedConcept = Schemas['ResolvedConcept'];

export type AttachmentUploadUrlRequest = Schemas['AttachmentUploadUrlRequest'];
export type AttachmentUploadUrlResponse = Schemas['AttachmentUploadUrlResponse'];
export type AttachmentConfirmRequest = Schemas['AttachmentConfirmRequest'];
export type AttachmentRead = Schemas['AttachmentRead'];
export type AttachmentDownloadUrlResponse = Schemas['AttachmentDownloadUrlResponse'];
export type MediaVariantRead = Schemas['MediaVariantRead'];
export type PresignedUrlResponse = Schemas['PresignedUrlResponse'];
