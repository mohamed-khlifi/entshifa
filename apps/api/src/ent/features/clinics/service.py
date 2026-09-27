"""Clinic, site and clinical-settings use cases (P1-01)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.audit.serialize import row_to_audit_dict
from ent.core.errors.exceptions import ConflictError, NotFoundError, ValidationError
from ent.core.repository.pagination import Page
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.attachments.repository import AttachmentRepository
from ent.features.clinics.models import Clinic, Site
from ent.features.clinics.repository import (
    ClinicRepository,
    SettingRepository,
    SiteFilter,
    SiteRepository,
)
from ent.features.clinics.resolver import SettingResolver
from ent.features.clinics.schemas.requests import (
    ClinicalSettingsPut,
    ClinicUpdate,
    SiteCreate,
    SiteUpdate,
)
from ent.features.clinics.schemas.responses import (
    ClinicalSettingsRead,
    ClinicRead,
    ResolvedSettingRead,
    SiteRead,
)
from ent.features.clinics.setting_keys import (
    all_clinical_setting_keys,
    validate_setting_value,
)


async def _clinic_read(session: AsyncSession, clinic: Clinic) -> ClinicRead:
    logo_public_id: str | None = None
    if clinic.logo_attachment_id is not None:
        attachment = await AttachmentRepository(
            session,
            clinic_id=clinic.id,
        ).get(clinic.logo_attachment_id)
        if attachment is not None:
            logo_public_id = attachment.public_id
    base = ClinicRead.model_validate(clinic)
    return base.model_copy(update={"logo_attachment_public_id": logo_public_id})


def _site_read(site: Site) -> SiteRead:
    return SiteRead.model_validate(site)


class ClinicService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._clinics = ClinicRepository(session)
        self._settings = SettingRepository(session)
        self._resolver = SettingResolver(session)
        self._audit = AuditRecorder(session)

    def _sites(self, clinic_id: int) -> SiteRepository:
        return SiteRepository(self._session, clinic_id=clinic_id)

    async def get_current_clinic(self, *, user: CurrentUser) -> ClinicRead:
        clinic = await self._clinics.get(user.clinic_id)
        if clinic is None:
            raise NotFoundError(resource="clinic", public_id=user.clinic_public_id)
        return await _clinic_read(self._session, clinic)

    async def update_current_clinic(
        self,
        *,
        user: CurrentUser,
        body: ClinicUpdate,
    ) -> ClinicRead:
        clinic = await self._clinics.get(user.clinic_id)
        if clinic is None:
            raise NotFoundError(resource="clinic", public_id=user.clinic_public_id)

        data = body.model_dump(exclude_unset=True)
        if "slug" in data and data["slug"] != clinic.slug:
            other = await self._clinics.get_by_slug(data["slug"])
            if other is not None and other.id != clinic.id:
                raise ConflictError(reason="slug_taken", slug=data["slug"])

        if "supported_locales" in data and data["supported_locales"] is not None:
            locales = data["supported_locales"]
            if not locales:
                raise ValidationError(reason="supported_locales_empty")
            default = data.get("default_locale", clinic.default_locale)
            if default not in locales:
                raise ValidationError(
                    reason="default_locale_not_supported",
                    defaultLocale=default,
                )

        if "default_locale" in data and "supported_locales" not in data:
            if data["default_locale"] not in clinic.supported_locales:
                raise ValidationError(
                    reason="default_locale_not_supported",
                    defaultLocale=data["default_locale"],
                )

        if "settings" in data and isinstance(data["settings"], dict):
            from ent.features.documents.letterhead import validate_document_settings

            await validate_document_settings(
                self._session,
                clinic_id=user.clinic_id,
                settings=data["settings"],
            )

        if "logo_attachment_public_id" in data:
            logo_public_id = data.pop("logo_attachment_public_id")
            if logo_public_id is None:
                clinic.logo_attachment_id = None
            else:
                attachment = await AttachmentRepository(
                    self._session,
                    clinic_id=user.clinic_id,
                ).get_by_public_id(logo_public_id)
                if attachment is None or attachment.category != "logo":
                    raise NotFoundError(
                        resource="attachment",
                        public_id=logo_public_id,
                    )
                clinic.logo_attachment_id = attachment.id

        before = row_to_audit_dict(clinic)
        for field, value in data.items():
            setattr(clinic, field, value)
        clinic.updated_by_id = user.user_id

        self._audit.record_write(
            action="update",
            entity=clinic,
            before=before,
            clinic_id=user.clinic_id,
        )
        await self._session.commit()
        await self._session.refresh(clinic)
        return await _clinic_read(self._session, clinic)

    async def list_sites(
        self,
        *,
        user: CurrentUser,
        search: str | None = None,
        is_primary: bool | None = None,
        city: str | None = None,
        sort: str | None = None,
        page: PaginationParams | None = None,
    ) -> PageSchema[SiteRead]:
        repo = self._sites(user.clinic_id)
        result: Page[Site] = await repo.list(
            filters=SiteFilter(search=search, is_primary=is_primary, city=city),
            sort=sort,
            page=page,
        )
        return result.to_schema(SiteRead)

    async def get_site(self, *, user: CurrentUser, public_id: str) -> SiteRead:
        site = await self._sites(user.clinic_id).get_by_public_id(public_id)
        if site is None:
            raise NotFoundError(resource="site", public_id=public_id)
        return _site_read(site)

    async def create_site(
        self,
        *,
        user: CurrentUser,
        body: SiteCreate,
    ) -> SiteRead:
        repo = self._sites(user.clinic_id)
        count = await repo.count_active()
        is_primary = body.is_primary or count == 0

        if is_primary:
            await repo.clear_primary_except(keep_id=None)

        site = Site(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            name=body.name,
            address_line1=body.address_line1,
            address_line2=body.address_line2,
            city=body.city,
            postal_code=body.postal_code,
            phone=body.phone,
            is_primary=is_primary,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await repo.add(site)
        self._audit.record_entity_create(site)
        await self._session.commit()
        await self._session.refresh(site)
        return _site_read(site)

    async def update_site(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: SiteUpdate,
    ) -> SiteRead:
        repo = self._sites(user.clinic_id)
        site = await repo.get_by_public_id(public_id)
        if site is None:
            raise NotFoundError(resource="site", public_id=public_id)

        data = body.model_dump(exclude_unset=True)
        make_primary = data.pop("is_primary", None)
        before = row_to_audit_dict(site)

        for field, value in data.items():
            setattr(site, field, value)

        if make_primary is True:
            await repo.clear_primary_except(keep_id=site.id)
            site.is_primary = True
        elif make_primary is False and site.is_primary:
            raise ValidationError(reason="cannot_unset_sole_primary")

        site.updated_by_id = user.user_id
        self._audit.record_entity_update(site, before=before)
        await self._session.commit()
        await self._session.refresh(site)
        return _site_read(site)

    async def delete_site(self, *, user: CurrentUser, public_id: str) -> None:
        repo = self._sites(user.clinic_id)
        site = await repo.get_by_public_id(public_id)
        if site is None:
            raise NotFoundError(resource="site", public_id=public_id)
        if site.is_primary:
            raise ValidationError(reason="cannot_delete_primary_site")

        before = row_to_audit_dict(site)
        await repo.soft_delete(site.id, by_user_id=user.user_id)
        self._audit.record_entity_delete(site, before=before)
        await self._session.commit()

    async def get_clinical_settings(self, *, user: CurrentUser) -> ClinicalSettingsRead:
        keys = sorted(all_clinical_setting_keys())
        resolved = await self._resolver.resolve_many(
            keys=keys,
            clinic_id=user.clinic_id,
            user_id=user.user_id,
        )
        return ClinicalSettingsRead(
            items=[
                ResolvedSettingRead(key=item.key, value=item.value, source=item.source)
                for item in resolved
            ],
        )

    async def put_clinical_settings(
        self,
        *,
        user: CurrentUser,
        body: ClinicalSettingsPut,
    ) -> ClinicalSettingsRead:
        for item in body.items:
            value = validate_setting_value(item.key, item.value)
            existing = await self._settings.get_scoped(
                key=item.key,
                clinic_id=user.clinic_id,
                user_id=None,
            )
            before = row_to_audit_dict(existing) if existing is not None else None
            row = await self._settings.upsert_scoped(
                key=item.key,
                value=value,
                clinic_id=user.clinic_id,
                user_id=None,
                by_user_id=user.user_id,
            )
            if before is None:
                self._audit.record_entity_create(row, clinic_id=user.clinic_id)
            else:
                self._audit.record_write(
                    action="update",
                    entity=row,
                    before=before,
                    clinic_id=user.clinic_id,
                )

        await self._session.commit()
        return await self.get_clinical_settings(user=user)
